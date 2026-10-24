using System.Collections;
using NUnit.Framework;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.TestTools;
using UnityEngine.UIElements;

public class CompanionRenderSmokeTest
{
    private GameObject cameraObject;
    private GameObject uiObject;
    private RenderTexture renderTexture;

    [UnityTest]
    public IEnumerator ShouldRenderCompanionUiWithUrp()
    {
        // Exercise the real UI assets without starting discovery or loading a user profile.
        cameraObject = new GameObject("Companion render test camera", typeof(Camera));
        Camera camera = cameraObject.GetComponent<Camera>();
        GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Common/CommonSceneObjects.prefab");
        EditorUtility.CopySerialized(prefab.GetComponentInChildren<Camera>(true), camera);
        UniversalAdditionalCameraData cameraData = cameraObject.AddComponent<UniversalAdditionalCameraData>();
        EditorUtility.CopySerialized(prefab.GetComponentInChildren<UniversalAdditionalCameraData>(true), cameraData);

        uiObject = new GameObject("Companion render test UI");
        uiObject.SetActive(false);
        UIDocument document = uiObject.AddComponent<UIDocument>();
        document.panelSettings = AssetDatabase.LoadAssetAtPath<PanelSettings>("Assets/UI Toolkit/CompanionAppPanelSettings.asset");
        document.visualTreeAsset = AssetDatabase.LoadAssetAtPath<VisualTreeAsset>("Assets/Scenes/MainScene/MainSceneUi.uxml");
        Assert.IsNotNull(document.panelSettings);
        Assert.IsNotNull(document.visualTreeAsset);
        uiObject.SetActive(true);

        for (int frame = 0; frame < 5; frame++)
        {
            yield return null;
        }

        // Batch-mode tests do not automatically render the Game view.
        renderTexture = new RenderTexture(64, 64, 24);
        renderTexture.Create();
        RenderPipeline.SubmitRenderRequest(camera,
            new UniversalRenderPipeline.SingleCameraRequest { destination = renderTexture });

        Assert.IsInstanceOf<UniversalRenderPipeline>(RenderPipelineManager.currentPipeline);
        Assert.IsNotNull(cameraData.scriptableRenderer);
        Assert.IsTrue(renderTexture.IsCreated());
        Assert.IsNotNull(document.rootVisualElement.panel);
        Assert.Greater(document.rootVisualElement.resolvedStyle.width, 0);
        Assert.Greater(document.rootVisualElement.resolvedStyle.height, 0);
        Assert.IsNotNull(document.rootVisualElement.Q<Button>("toggleRecordingButton"));
        Assert.IsNotNull(document.rootVisualElement.Q<TextField>("clientNameTextField"));
        LogAssert.NoUnexpectedReceived();
    }

    [UnityTearDown]
    public IEnumerator TearDown()
    {
        Object.Destroy(uiObject);
        Object.Destroy(cameraObject);
        if (renderTexture != null)
        {
            renderTexture.Release();
            Object.Destroy(renderTexture);
        }
        yield return null;
    }
}
