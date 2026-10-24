using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using NUnit.Framework;
using ProTrans;
using UniInject;
using UnityEngine;
using UnityEngine.TestTools;
using UnityEngine.UIElements;
using static ConditionUtils;
using static SceneConditionTestUtils;
using static VisualElementTestUtils;

public abstract class SongSelectLocalizedPlaylistTest : AbstractPlayModeTest
{
    protected abstract string CultureName { get; }
    private CultureInfo previousCulture;

    [Inject(SearchMethod = SearchMethods.FindObjectOfType)]
    protected SongSelectSceneControl songSelectSceneControl;

    [Inject]
    protected PlaylistManager playlistManager;

    protected override string TestSceneName => EScene.SongSelectScene.ToString();

    protected override List<string> GetRelativeTestSongFilePaths()
    {
        return new List<string> { "SongSearchTestSongs/Default.txt" };
    }

    protected override void ConfigureTestSettings(TestSettings settings)
    {
        base.ConfigureTestSettings(settings);
        previousCulture = TranslationConfig.Singleton.CurrentCultureInfo;
        settings.CultureInfoName = CultureName;
        TranslationConfig.Singleton.CurrentCultureInfo = new CultureInfo(CultureName);
    }

    [TearDown]
    public void RestoreCulture()
    {
        if (previousCulture != null)
        {
            TranslationConfig.Singleton.CurrentCultureInfo = previousCulture;
        }
    }

    [UnityTest]
    public IEnumerator ShouldDefaultAndResetToAllSongs() => ShouldDefaultAndResetToAllSongsAsync();

    private async Awaitable ShouldDefaultAndResetToAllSongsAsync()
    {
        LogAssertUtils.IgnoreFailingMessages();
        await ExpectSceneAsync(EScene.SongSelectScene);
        SongSelectionPlaylistChooserControl chooser = songSelectSceneControl.SongSelectionPlaylistChooserControl;
        Assert.IsInstanceOf<UltraStarAllSongsPlaylist>(chooser.Selection.Value, CultureName);
        DropdownField dropdown = await GetElementAsync<DropdownField>(R.UxmlNames.playlistDropdownField);
        Assert.AreEqual(Translation.Get(R.Messages.playlistName_allSongs).Value, dropdown.choices[0]);
        await WaitForConditionAsync(() => songSelectSceneControl.songRouletteControl.SongEntries.Count == 1);

        UltraStarPlaylist favorites = playlistManager.FavoritesPlaylist;
        dropdown.value = favorites.Name;
        Assert.AreSame(favorites, chooser.Selection.Value);
        chooser.Reset();
        Assert.IsInstanceOf<UltraStarAllSongsPlaylist>(chooser.Selection.Value);
        chooser.TogglePlaylist(favorites);
        Assert.AreSame(favorites, chooser.Selection.Value);
        chooser.TogglePlaylist(favorites);
        Assert.IsInstanceOf<UltraStarAllSongsPlaylist>(chooser.Selection.Value);
    }

    public class SongSelectLocalizedPlaylistTestEnglish : SongSelectLocalizedPlaylistTest
    {
        protected override string CultureName => "en";
    }

    public class SongSelectLocalizedPlaylistTestSimplifiedChinese : SongSelectLocalizedPlaylistTest
    {
        protected override string CultureName => "zh";
    }

    public class SongSelectLocalizedPlaylistTestTraditionalChinese : SongSelectLocalizedPlaylistTest
    {
        protected override string CultureName => "zh-TW";
    }

    public class SongSelectLocalizedPlaylistTestJapanese : SongSelectLocalizedPlaylistTest
    {
        protected override string CultureName => "ja";
    }
}
