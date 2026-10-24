using System;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using NUnit.Framework;

public class ArchiveExtractionTest
{
    private string testFolder;
    private string archivePath;
    private string targetFolder;
    private int mainThreadId;

    [SetUp]
    public void SetUp()
    {
        testFolder = Path.Combine(Path.GetTempPath(), "song-archive-test-" + Guid.NewGuid());
        Directory.CreateDirectory(testFolder);
        archivePath = Path.Combine(testFolder, "songs.ZIP");
        targetFolder = Path.Combine(testFolder, "extracted");
        mainThreadId = Thread.CurrentThread.ManagedThreadId;
    }

    [TearDown]
    public void TearDown()
    {
        Directory.Delete(testFolder, true);
    }

    [Test]
    public async Task ShouldExtractNestedUnicodeFilesWithoutDirectoryEntries()
    {
        const string songText = "#TITLE:Test\n#ARTIST:Test Artist\n#BPM:120\n#MP3:audio.mp3\n: 0 4 60 Test\nE\n";
        using (ZipArchive archive = ZipFile.Open(archivePath, ZipArchiveMode.Create))
        {
            WriteEntry(archive, "songs-master/\u6e2c\u8a66\u6b4c\u66f2/song.txt", songText);
            WriteEntry(archive, "songs-master/\u6e2c\u8a66\u6b4c\u66f2/audio.mp3", "test media bytes");
            archive.CreateEntry("songs-master/empty/");
        }
        ExtractArchiveControl control = new(archivePath, targetFolder);
        await control.ExtractArchiveAsync();

        Assert.AreEqual(songText, File.ReadAllText(Path.Combine(targetFolder, "songs-master", "\u6e2c\u8a66\u6b4c\u66f2", "song.txt")));
        Assert.AreEqual("test media bytes", File.ReadAllText(Path.Combine(targetFolder, "songs-master", "\u6e2c\u8a66\u6b4c\u66f2", "audio.mp3")));
        Assert.IsTrue(Directory.Exists(Path.Combine(targetFolder, "songs-master", "empty")));
        Assert.AreEqual(100, control.Progress.ProgressInPercent);
        Assert.AreEqual(mainThreadId, Thread.CurrentThread.ManagedThreadId);
        Assert.IsTrue(File.Exists(archivePath), "Keep the downloaded archive available for retry.");
    }

    [Test]
    public async Task ShouldOverwriteImportedFilesButPreserveOtherSongs()
    {
        Directory.CreateDirectory(targetFolder);
        File.WriteAllText(Path.Combine(targetFolder, "song.txt"), "old");
        File.WriteAllText(Path.Combine(targetFolder, "unrelated.txt"), "keep");
        using (ZipArchive archive = ZipFile.Open(archivePath, ZipArchiveMode.Create))
        {
            WriteEntry(archive, "song.txt", "new");
        }
        await new ExtractArchiveControl(archivePath, targetFolder).ExtractArchiveAsync();
        Assert.AreEqual("new", File.ReadAllText(Path.Combine(targetFolder, "song.txt")));
        Assert.AreEqual("keep", File.ReadAllText(Path.Combine(targetFolder, "unrelated.txt")));
    }

    [TestCase("../escaped.txt")]
    [TestCase("folder/../../escaped.txt")]
    [TestCase("..\\escaped.txt")]
    [TestCase("/escaped.txt")]
    public async Task ShouldRejectPathsOutsideTheExtractionFolder(string entryName)
    {
        using (ZipArchive archive = ZipFile.Open(archivePath, ZipArchiveMode.Create))
        {
            WriteEntry(archive, entryName, "must not escape");
        }
        InvalidDataException exception = await ExtractExpectingFailure<InvalidDataException>(archivePath);
        StringAssert.Contains("outside the extraction folder", exception.Message);
        Assert.AreEqual(mainThreadId, Thread.CurrentThread.ManagedThreadId);
        Assert.IsFalse(File.Exists(Path.Combine(testFolder, "escaped.txt")));
        Assert.IsFalse(Directory.Exists(targetFolder));
    }

    [Test]
    public async Task ShouldReportInvalidZipAndReturnToMainThread()
    {
        File.WriteAllText(archivePath, "not a zip archive");
        await ExtractExpectingFailure<InvalidDataException>(archivePath);
        Assert.AreEqual(mainThreadId, Thread.CurrentThread.ManagedThreadId);
        Assert.IsFalse(Directory.Exists(targetFolder));
    }

    [Test]
    public async Task ShouldReportMissingArchive()
    {
        await ExtractExpectingFailure<FileNotFoundException>(archivePath);
    }

    [Test]
    public async Task ShouldReportUnsupportedArchiveInsteadOfSuccess()
    {
        string unsupportedPath = Path.Combine(testFolder, "songs.7z");
        File.WriteAllText(unsupportedPath, "unsupported");
        await ExtractExpectingFailure<NotSupportedException>(unsupportedPath);
        Assert.AreEqual(mainThreadId, Thread.CurrentThread.ManagedThreadId);
    }

    [Test]
    public async Task ShouldHandleEmptyZip()
    {
        using (ZipFile.Open(archivePath, ZipArchiveMode.Create))
        {
        }
        await new ExtractArchiveControl(archivePath, targetFolder).ExtractArchiveAsync();
        Assert.IsTrue(Directory.Exists(targetFolder));
        Assert.IsFalse(Directory.EnumerateFileSystemEntries(targetFolder).Any());
    }

    private static void WriteEntry(ZipArchive archive, string name, string text)
    {
        using StreamWriter writer = new(archive.CreateEntry(name).Open());
        writer.Write(text);
    }

    private async Task<T> ExtractExpectingFailure<T>(string path) where T : Exception
    {
        try
        {
            await new ExtractArchiveControl(path, targetFolder).ExtractArchiveAsync();
        }
        catch (T exception)
        {
            return exception;
        }
        throw new AssertionException($"Expected {typeof(T).Name}, but extraction succeeded.");
    }
}
