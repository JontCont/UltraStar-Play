using System;
using System.IO;
using System.IO.Compression;
using ICSharpCode.SharpZipLib.Tar;
using UnityEngine;

public class ExtractArchiveControl
{
    private readonly string archivePath;
    private readonly string targetFolder;

    private long totalZipEntryCount;
    private long extractedZipEntryCount;

    private long totalTarFileSizeInBytes;
    private long extractedTarFileEntrySizeInBytes;

    public ExtractArchiveProgress Progress
    {
        get
        {
            if (totalZipEntryCount > 0)
            {
                return new ExtractArchiveProgress(extractedZipEntryCount, totalZipEntryCount);
            }
            else if (totalTarFileSizeInBytes > 0)
            {
                return new ExtractArchiveProgress(extractedTarFileEntrySizeInBytes, totalTarFileSizeInBytes);
            }
            return new ExtractArchiveProgress(0, 0);
        }
    }

    public ExtractArchiveControl(string archivePath, string targetFolder)
    {
        this.archivePath = archivePath;
        this.targetFolder = targetFolder;
    }

    public async Awaitable ExtractArchiveAsync()
    {
        if (!FileUtils.Exists(archivePath))
        {
            throw new FileNotFoundException(archivePath);
        }

        // Extract archive on background thread
        await Awaitable.BackgroundThreadAsync();

        try
        {
            if (archivePath.EndsWith(".tar", StringComparison.OrdinalIgnoreCase))
            {
                await ExtractTarArchiveAsync();
            }
            else if (archivePath.EndsWith(".zip", StringComparison.OrdinalIgnoreCase))
            {
                ExtractZipArchive();
            }
            else
            {
                throw new NotSupportedException($"Unsupported archive format: {Path.GetExtension(archivePath)}");
            }
        }
        finally
        {
            await Awaitable.MainThreadAsync();
        }
    }

    private void ExtractZipArchive()
    {
        using Stream archiveStream = File.OpenRead(archivePath);
        using ZipArchive archive = new(archiveStream, ZipArchiveMode.Read);
        extractedZipEntryCount = 0;
        totalZipEntryCount = archive.Entries.Count;

        // Workaround for Windows path length limit: Extract to temporary folder with shorter path. 
        // Use Path.GetTempPath because Unity's Application.persistentDataPath can only be called on the main thread.
        string extractFolder = PlatformUtils.IsWindows ? $"{Path.GetTempPath()}/extract-{Guid.NewGuid()}" : targetFolder;

        try
        {
            Directory.CreateDirectory(extractFolder);
            foreach (ZipArchiveEntry entry in archive.Entries)
            {
                ExtractZipEntry(entry, extractFolder);
                extractedZipEntryCount++;
            }

            if (PlatformUtils.IsWindows)
            {
                DirectoryUtils.CopyAll(extractFolder, targetFolder);
            }
        }
        finally
        {
            if (PlatformUtils.IsWindows && Directory.Exists(extractFolder))
            {
                Directory.Delete(extractFolder, true);
            }
        }
    }

    private void ExtractZipEntry(ZipArchiveEntry entry, string targetFolder)
    {
        string rootPath = Path.GetFullPath(targetFolder)
            .TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar) + Path.DirectorySeparatorChar;
        string entryPath = entry.FullName.Replace('\\', Path.DirectorySeparatorChar).Replace('/', Path.DirectorySeparatorChar);
        string targetPath = Path.GetFullPath(Path.Combine(rootPath, entryPath));
        StringComparison comparison = PlatformUtils.IsWindows ? StringComparison.OrdinalIgnoreCase : StringComparison.Ordinal;
        if (Path.IsPathRooted(entryPath) || !targetPath.StartsWith(rootPath, comparison))
        {
            throw new InvalidDataException($"Archive entry is outside the extraction folder: {entry.FullName}");
        }
        if (entryPath.EndsWith(Path.DirectorySeparatorChar.ToString(), StringComparison.Ordinal))
        {
            Directory.CreateDirectory(targetPath);
            return;
        }

        Debug.Log($"Extracting ZIP entry {entry.FullName}");
        Directory.CreateDirectory(Path.GetDirectoryName(targetPath));
        using Stream entryStream = entry.Open();
        using FileStream targetStream = File.Create(targetPath);
        entryStream.CopyTo(targetStream);
    }

    private async Awaitable ExtractTarArchiveAsync()
    {
        await using Stream archiveStream = File.OpenRead(archivePath);
        using TarArchive archive = TarArchive.CreateInputTarArchive(archiveStream);
        archive.ProgressMessageEvent += OnExtractTarArchiveProgress;

        totalTarFileSizeInBytes = new FileInfo(archivePath).Length;
        archive.ExtractContents(targetFolder);
    }

    private void OnExtractTarArchiveProgress(TarArchive archive, TarEntry entry, string message)
    {
        extractedTarFileEntrySizeInBytes += entry.Size;
    }
}
