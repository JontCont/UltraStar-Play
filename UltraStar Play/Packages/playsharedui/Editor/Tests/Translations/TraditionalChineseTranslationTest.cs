using System;
using System.Globalization;
using System.Linq;
using System.Text.RegularExpressions;
using NUnit.Framework;
using ProTrans;
using UnityEditor;
using UnityEngine;
using UnityEngine.TextCore;
using UnityEngine.TextCore.LowLevel;
using UnityEngine.TextCore.Text;
using UnityEngine.UIElements;
using TextAsset = UnityEngine.TextAsset;

public class TraditionalChineseTranslationTest
{
    private TranslationConfig previousConfig;

    [SetUp]
    public void SetUp()
    {
        previousConfig = TranslationConfig.Singleton;
        TranslationConfig.Singleton = new TranslationConfig
        {
            CurrentCultureInfo = new CultureInfo("zh-TW"),
            PropertiesFileProvider = new CachingPropertiesFileProvider(new ResourcesFolderPropertiesFileProvider()),
        };
    }

    [TearDown]
    public void TearDown()
    {
        TranslationConfig.Singleton = previousConfig;
    }

    [Test]
    public void ShouldImportRegionSpecificCatalogue()
    {
        TextAsset asset = Resources.Load<TextAsset>("Translations/messages_zh_TW");
        Assert.IsNotNull(asset);
        Assert.AreEqual("messages_zh_TW.properties", System.IO.Path.GetFileName(AssetDatabase.GetAssetPath(asset)));
        Assert.AreEqual("_zh_TW", PropertiesFileParser.GetLanguageAndRegionSuffix(new CultureInfo("zh-TW")));
        Assert.IsNotNull(Translation.GetPropertiesFile(new CultureInfo("zh-TW")));
    }

    [Test]
    public void ShouldTranslateEveryDefaultKeyWithoutDuplicates()
    {
        TextAsset englishAsset = Resources.Load<TextAsset>("Translations/messages");
        TextAsset traditionalAsset = Resources.Load<TextAsset>("Translations/messages_zh_TW");
        Assert.IsNotNull(englishAsset);
        Assert.IsNotNull(traditionalAsset);
        PropertiesFile english = PropertiesFileParser.ParseText(englishAsset.text, new CultureInfo("en"));
        PropertiesFile traditional = PropertiesFileParser.ParseText(traditionalAsset.text, new CultureInfo("zh-TW"));
        CollectionAssert.AreEquivalent(english.Dictionary.Keys, traditional.Dictionary.Keys);

        string[] rawKeys = traditionalAsset.text.Split('\n')
            .Where(line => !string.IsNullOrWhiteSpace(line) && !line.StartsWith("#") && !line.StartsWith("!"))
            .Select(line => line.Substring(0, line.IndexOf('=')))
            .ToArray();
        Assert.AreEqual(rawKeys.Length, rawKeys.Distinct(StringComparer.OrdinalIgnoreCase).Count());

        foreach (string key in english.Dictionary.Keys)
        {
            string source = english.Dictionary[key];
            string translated = traditional.Dictionary[key];
            Assert.IsFalse(string.IsNullOrWhiteSpace(translated), key);
            foreach (string pattern in new[] { @"\{[^{}]+\}", @"<[^>]+>", "\n", @"https?://[^\s<>]+" })
            {
                CollectionAssert.AreEquivalent(
                    Regex.Matches(source, pattern).Cast<Match>().Select(match => match.Value),
                    Regex.Matches(translated, pattern).Cast<Match>().Select(match => match.Value),
                    $"{key}: {pattern}");
            }
        }
    }

    [TestCase("mainScene_button_sing", "開始唱歌")]
    [TestCase("options_game_title", "遊戲設定")]
    [TestCase("songSelectScene_title", "選歌")]
    [TestCase("songEditor_sideBar_save", "儲存")]
    [TestCase("companionApp_songList_show", "顯示歌曲清單")]
    public void ShouldResolveTraditionalChineseAtRuntime(string key, string expected)
    {
        Assert.AreEqual(expected, Translation.Get(key).Value);
    }

    [Test]
    public void ShouldFormatPlaceholdersAtRuntime()
    {
        Assert.AreEqual("下一首：測試歌曲", Translation.Get("songQueue_nextEntry", "value", "測試歌曲").Value);
    }

    [Test]
    public void ShouldOfferBothChineseVariantsAlongsideEnglishAndJapanese()
    {
        DropdownField dropdown = new DropdownField();
        LanguageChooserControl chooser = new LanguageChooserControl(dropdown);
        string[] cultures = chooser.Items.Select(culture => culture.Name).ToArray();
        foreach (string name in new[] { "en", "ja", "zh", "zh-TW" })
        {
            CollectionAssert.Contains(cultures, name);
        }
        Assert.AreEqual("zh-TW", chooser.Selection.Name);
        Assert.AreEqual("Chinese (Traditional) - 繁體中文", dropdown.value);
        CollectionAssert.Contains(dropdown.choices, "Chinese (Simplified)");
        chooser.Selection = new CultureInfo("zh");
        Assert.AreEqual("Chinese (Simplified)", dropdown.value);
        chooser.Selection = new CultureInfo("zh-TW");
        Assert.AreEqual("Chinese (Traditional) - 繁體中文", dropdown.value);
    }

    [Test]
    public void ShouldProvideTraditionalGlyphsInExistingFallbackFont()
    {
        const string fontsPath = "Packages/playsharedui/Runtime/Fonts/";
        PanelTextSettings settings = AssetDatabase.LoadAssetAtPath<PanelTextSettings>(
            fontsPath + "UltraStarPlayTextSettings.asset");
        FontAsset fontAsset = AssetDatabase.LoadAssetAtPath<FontAsset>(
            fontsPath + "Noto_Sans_TC/NotoSansTC-Regular SDF.asset");
        Assert.IsNotNull(settings);
        Assert.IsNotNull(fontAsset);
        CollectionAssert.Contains(settings.fallbackFontAssets, fontAsset);
        Assert.AreEqual(AtlasPopulationMode.Dynamic, fontAsset.atlasPopulationMode);
        Assert.IsNotNull(fontAsset.sourceFontFile);

        Assert.AreEqual(FontEngineError.Success, FontEngine.InitializeFontEngine());
        try
        {
            Assert.AreEqual(FontEngineError.Success, FontEngine.LoadFontFace(fontAsset.sourceFontFile, 32));
            string values = string.Join("", Translation.GetPropertiesFile(new CultureInfo("zh-TW")).Dictionary.Values);
            foreach (char character in values.Distinct().Where(character => character >= '\u3400' && character <= '\u9fff'))
            {
                Assert.IsTrue(FontEngine.TryGetGlyphWithUnicodeValue(character, GlyphLoadFlags.LOAD_DEFAULT, out Glyph glyph),
                    $"Noto Sans TC is missing U+{(int)character:X4}");
                Assert.AreNotEqual(0u, glyph.index);
            }
        }
        finally
        {
            FontEngine.UnloadFontFace();
        }
    }
}
