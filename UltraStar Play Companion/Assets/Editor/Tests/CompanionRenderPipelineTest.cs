using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.UIElements;

public class CompanionRenderPipelineTest
{
    private const string PipelinePath = "Assets/RenderPipeline/CompanionRenderPipeline.asset";

    [Test]
    public void ShouldUseLocalUrpAtEveryQualityLevel()
    {
        UniversalRenderPipelineAsset pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(PipelinePath);
        Assert.IsNotNull(pipeline);
        Assert.AreSame(pipeline, GraphicsSettings.defaultRenderPipeline);
        for (int quality = 0; quality < QualitySettings.names.Length; quality++)
        {
            RenderPipelineAsset qualityPipeline = QualitySettings.GetRenderPipelineAssetAt(quality);
            Assert.AreSame(pipeline, qualityPipeline != null ? qualityPipeline : GraphicsSettings.defaultRenderPipeline,
                $"Quality level {QualitySettings.names[quality]} must use Companion URP.");
        }
    }

    [Test]
    public void ShouldUseLightweightForwardRenderer()
    {
        UniversalRenderPipelineAsset pipeline = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(PipelinePath);
        Assert.IsNotNull(pipeline);
        Assert.IsFalse(pipeline.supportsHDR);
        Assert.AreEqual(1, pipeline.msaaSampleCount);
        Assert.AreEqual(1f, pipeline.renderScale);
        Assert.IsFalse(pipeline.supportsCameraDepthTexture);
        Assert.IsFalse(pipeline.supportsCameraOpaqueTexture);
        Assert.AreEqual(0f, pipeline.shadowDistance);
        Assert.AreEqual(1, pipeline.rendererDataList.Length);
        Assert.IsInstanceOf<UniversalRendererData>(pipeline.rendererDataList[0]);
        UniversalRendererData renderer = (UniversalRendererData)pipeline.rendererDataList[0];
        Assert.AreEqual("Assets/RenderPipeline/CompanionRenderer.asset", AssetDatabase.GetAssetPath(renderer));
        Assert.AreEqual(RenderingMode.Forward, renderer.renderingMode);
        Assert.IsEmpty(renderer.rendererFeatures);
    }

    [Test]
    public void ShouldConfigureExistingCameraForUrp()
    {
        GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Common/CommonSceneObjects.prefab");
        Assert.IsNotNull(prefab);
        Camera camera = prefab.GetComponentInChildren<Camera>(true);
        Assert.IsNotNull(camera);
        Assert.IsTrue(camera.orthographic);
        UniversalAdditionalCameraData cameraData = camera.GetComponent<UniversalAdditionalCameraData>();
        Assert.IsNotNull(cameraData);
        Assert.IsFalse(cameraData.renderPostProcessing);
        Assert.IsFalse(cameraData.renderShadows);
        Assert.IsFalse(cameraData.requiresDepthTexture);
        Assert.IsFalse(cameraData.requiresColorTexture);
    }

    [TestCase("MenuUi")]
    [TestCase("SongDetailsUi")]
    public void ShouldParseScrollPhysicsAsInvariantDecimals(string layoutName)
    {
        VisualTreeAsset layout = AssetDatabase.LoadAssetAtPath<VisualTreeAsset>($"Assets/Scenes/MainScene/{layoutName}.uxml");
        Assert.IsNotNull(layout);
        ScrollView scrollView = layout.CloneTree().Q<ScrollView>();
        Assert.IsNotNull(scrollView);
        Assert.AreEqual(0.135f, scrollView.scrollDecelerationRate, 0.00001f);
        Assert.AreEqual(0.1f, scrollView.elasticity, 0.00001f);
    }
}
