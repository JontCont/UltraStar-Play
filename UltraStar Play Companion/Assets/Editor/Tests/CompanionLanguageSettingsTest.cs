using System.Globalization;
using NUnit.Framework;

public class CompanionLanguageSettingsTest
{
    [TestCase("en")]
    [TestCase("ja")]
    [TestCase("zh")]
    [TestCase("zh-TW")]
    public void ShouldPreserveLanguageAfterSettingsSerialization(string cultureName)
    {
        Settings settings = new Settings { CultureInfoName = cultureName };
        Settings restoredSettings = JsonConverter.FromJson<Settings>(JsonConverter.ToJson(settings));
        Assert.AreEqual(cultureName, restoredSettings.CultureInfoName);
        Assert.AreEqual(cultureName, new CultureInfo(restoredSettings.CultureInfoName).Name);
    }
}
