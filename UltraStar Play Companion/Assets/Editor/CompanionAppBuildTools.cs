using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

public static class CompanionAppBuildTools
{
    private static readonly string appName = "UltraStar Play Companion";

    [MenuItem("Build/Configure Companion URP")]
    public static void ConfigureRenderPipeline()
    {
        const string folder = "Assets/RenderPipeline";
        const string rendererPath = folder + "/CompanionRenderer.asset";
        const string pipelinePath = folder + "/CompanionRenderPipeline.asset";
        const string prefabPath = "Assets/Common/CommonSceneObjects.prefab";

        if (!AssetDatabase.IsValidFolder(folder))
        {
            AssetDatabase.CreateFolder("Assets", "RenderPipeline");
        }

        UniversalRendererData renderer = AssetDatabase.LoadAssetAtPath<UniversalRendererData>(rendererPath);
        if (renderer == null)
        {
            renderer = ScriptableObject.CreateInstance<UniversalRendererData>();
            AssetDatabase.CreateAsset(renderer, rendererPath);
        }

        UniversalRenderPipelineAsset pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(pipelinePath);
        if (pipeline == null)
        {
            pipeline = UniversalRenderPipelineAsset.Create(renderer);
            pipeline.supportsHDR = false;
            pipeline.msaaSampleCount = 1;
            pipeline.supportsCameraDepthTexture = false;
            pipeline.supportsCameraOpaqueTexture = false;
            pipeline.shadowDistance = 0;
            AssetDatabase.CreateAsset(pipeline, pipelinePath);
        }

        GraphicsSettings.defaultRenderPipeline = pipeline;
        int originalQuality = QualitySettings.GetQualityLevel();
        try
        {
            for (int quality = 0; quality < QualitySettings.names.Length; quality++)
            {
                QualitySettings.SetQualityLevel(quality, false);
                QualitySettings.renderPipeline = null;
            }
        }
        finally
        {
            QualitySettings.SetQualityLevel(originalQuality, false);
        }

        GameObject prefab = PrefabUtility.LoadPrefabContents(prefabPath);
        try
        {
            Camera camera = prefab.GetComponentInChildren<Camera>(true);
            if (camera == null)
            {
                throw new System.InvalidOperationException("Companion common prefab has no camera.");
            }
            UniversalAdditionalCameraData cameraData = camera.GetUniversalAdditionalCameraData();
            cameraData.renderPostProcessing = false;
            cameraData.renderShadows = false;
            cameraData.requiresDepthTexture = false;
            cameraData.requiresColorTexture = false;
            cameraData.SetRenderer(0);
            PrefabUtility.SaveAsPrefabAsset(prefab, prefabPath);
        }
        finally
        {
            PrefabUtility.UnloadPrefabContents(prefab);
        }

        AssetDatabase.SaveAssets();
        Debug.Log($"Companion URP configured: {pipelinePath}, {QualitySettings.names.Length} quality levels inherit the default.");
    }

    [MenuItem("Build/Windows64")]
    public static void BuildWindows64()
    {
        CustomBuildOptions customBuildOptions = CreateCustomBuildOptions(BuildTarget.StandaloneWindows64);
        customBuildOptions.compressOutputFolderToZipFile = false;
        BuildUtils.PerformCustomBuild(customBuildOptions);
    }

    [MenuItem("Build/Android - Build apk")]
    public static void BuildAndroidApk()
    {
        BuildUtils.PerformCustomBuild(CreateCustomBuildOptions(BuildTarget.Android));
    }

    [MenuItem("Build/Android - Build and run apk")]
    public static void BuildAndRunAndroidApk()
    {
        CustomBuildOptions customBuildOptions = CreateCustomBuildOptions(BuildTarget.Android);
        customBuildOptions.buildOptions = BuildOptions.AutoRunPlayer;
        BuildUtils.PerformCustomBuild(customBuildOptions);
    }

    [MenuItem("Build/Android - Build signed app bundle (aab)")]
    public static void BuildSignedAndroidAppBundle()
    {
        CustomBuildOptions customBuildOptions = CreateCustomBuildOptions(BuildTarget.Android);
        customBuildOptions.configureKeystoreForAndroidBuild = true;
        customBuildOptions.buildAppBundleForGooglePlay = true;
        BuildUtils.PerformCustomBuild(customBuildOptions);
    }

    [MenuItem("Build/Android - Build and run signed app bundle (aab)")]
    public static void BuildAndRunSignedAndroidAppBundle()
    {
        CustomBuildOptions customBuildOptions = CreateCustomBuildOptions(BuildTarget.Android);
        customBuildOptions.buildOptions = BuildOptions.AutoRunPlayer;
        customBuildOptions.configureKeystoreForAndroidBuild = true;
        customBuildOptions.buildAppBundleForGooglePlay = true;
        BuildUtils.PerformCustomBuild(customBuildOptions);
    }

    [MenuItem("Build/Android - Push apk to device")]
    public static void PushToAndroid()
    {
        BuildUtils.PushApkToDevice(appName);
    }

    [MenuItem("Build/iOS")]
    public static void BuildIOS()
    {
        BuildUtils.PerformCustomBuild(CreateCustomBuildOptions(BuildTarget.iOS));
    }

    private static CustomBuildOptions CreateCustomBuildOptions(BuildTarget buildTarget)
    {
        CustomBuildOptions customBuildOptions = new CustomBuildOptions(appName, buildTarget);
        customBuildOptions.compressOutputFolderToZipFile = true;
        return customBuildOptions;
    }
}
