using NUnit.Framework;

public class PitchIndicatorVisibilityTest
{
    [Test]
    public void EasyShowsPitchWithoutPitchIndicatorSetting()
    {
        Settings settings = new() { ShowPitchIndicator = false };
        PlayerProfile playerProfile = new("TestPlayer1", EDifficulty.Easy);

        Assert.IsTrue(PlayerMicPitchTracker.IsPitchIndicatorEnabled(settings, playerProfile));
    }

    [Test]
    public void MediumAndHardFollowPitchIndicatorSetting()
    {
        Settings disabledSettings = new() { ShowPitchIndicator = false };
        Settings enabledSettings = new() { ShowPitchIndicator = true };

        Assert.IsFalse(PlayerMicPitchTracker.IsPitchIndicatorEnabled(disabledSettings, new PlayerProfile("TestPlayer1", EDifficulty.Medium)));
        Assert.IsFalse(PlayerMicPitchTracker.IsPitchIndicatorEnabled(disabledSettings, new PlayerProfile("TestPlayer1", EDifficulty.Hard)));
        Assert.IsTrue(PlayerMicPitchTracker.IsPitchIndicatorEnabled(enabledSettings, new PlayerProfile("TestPlayer1", EDifficulty.Medium)));
        Assert.IsTrue(PlayerMicPitchTracker.IsPitchIndicatorEnabled(enabledSettings, new PlayerProfile("TestPlayer1", EDifficulty.Hard)));
    }

    [Test]
    public void EasyWithPitchIndicatorSettingStillEnabled()
    {
        Settings settings = new() { ShowPitchIndicator = true };
        PlayerProfile playerProfile = new("TestPlayer1", EDifficulty.Easy);

        Assert.IsTrue(PlayerMicPitchTracker.IsPitchIndicatorEnabled(settings, playerProfile));
    }
}
