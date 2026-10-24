using System.Linq;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using UnityEngine.TextCore;
using UnityEngine.TextCore.LowLevel;
using UnityEngine.TextCore.Text;
using TextAsset = UnityEngine.TextAsset;

public class CjkFontAtlasTest
{
    [TestCase("Noto_Sans_JP/NotoSansJP-VariableFont_wght")]
    [TestCase("Noto_Sans_JP/static/NotoSansJP-Regular")]
    [TestCase("Noto_Sans_JP/static/NotoSansJP-Bold")]
    [TestCase("Noto_Sans_JP/static/NotoSansJP-ExtraBold")]
    [TestCase("Noto_Sans_KR/NotoSansKR-Regular")]
    [TestCase("Noto_Sans_KR/NotoSansKR-Bold")]
    [TestCase("Noto_Sans_SC/NotoSansSC-Regular")]
    [TestCase("Noto_Sans_SC/NotoSansSC-Bold")]
    [TestCase("Noto_Sans_TC/NotoSansTC-Regular")]
    [TestCase("Noto_Sans_TC/NotoSansTC-Bold")]
    public void ShouldPackChineseAndJapaneseAcrossMultipleAtlasPages(string fontPath)
    {
        FontAsset productionFont = AssetDatabase.LoadAssetAtPath<FontAsset>(
            $"Packages/playsharedui/Runtime/Fonts/{fontPath} SDF.asset");
        Assert.IsNotNull(productionFont);
        Assert.IsNotNull(productionFont.sourceFontFile);
        string catalogueText = string.Join("", new[] { "zh", "zh_TW", "ja" }
            .Select(locale => Resources.Load<TextAsset>($"Translations/messages_{locale}").text));
        char[] characters = catalogueText.Distinct()
            .Where(character => character >= '\u3000' && character <= '\u9fff')
            .ToArray();

        Assert.AreEqual(FontEngineError.Success, FontEngine.InitializeFontEngine());
        try
        {
            Assert.AreEqual(FontEngineError.Success, FontEngine.LoadFontFace(productionFont.sourceFontFile,
                (int)productionFont.faceInfo.pointSize));
            characters = characters.Where(character =>
                FontEngine.TryGetGlyphWithUnicodeValue(character, GlyphLoadFlags.LOAD_DEFAULT, out Glyph glyph)
                && glyph.index != 0).ToArray();
        }
        finally
        {
            FontEngine.UnloadFontFace();
        }
        Assert.Greater(characters.Length, 500, "Use enough supported characters to exercise atlas capacity.");

        FontAsset temporaryFont = FontAsset.CreateFontAsset(productionFont.sourceFontFile,
            (int)productionFont.faceInfo.pointSize, productionFont.atlasPadding, productionFont.atlasRenderMode,
            productionFont.atlasWidth, productionFont.atlasHeight, productionFont.atlasPopulationMode,
            productionFont.isMultiAtlasTexturesEnabled);
        Assert.IsNotNull(temporaryFont);
        try
        {
            Assert.IsTrue(temporaryFont.TryAddCharacters(new string(characters), out string missingCharacters),
                $"{fontPath}: could not pack {missingCharacters?.Length ?? 0} supported characters.");
            Assert.IsTrue(string.IsNullOrEmpty(missingCharacters));
            Assert.Greater(temporaryFont.atlasTextureCount, 1, "The test must exercise additional atlas pages.");
            Assert.IsTrue(new SerializedObject(productionFont).FindProperty("m_ClearDynamicDataOnBuild").boolValue,
                "Do not ship Editor-populated atlas caches.");
        }
        finally
        {
            foreach (Texture2D texture in temporaryFont.atlasTextures)
            {
                if (texture != null)
                {
                    Object.DestroyImmediate(texture);
                }
            }
            Object.DestroyImmediate(temporaryFont.material);
            Object.DestroyImmediate(temporaryFont);
        }
    }
}
