using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using System.Net.Sockets;
using System.Text;
using System.IO;
using System;

public class Extractor : MonoBehaviour
{ 
    public Transform headTracker;
    public Transform rightShoulderTracker; 
    public Transform leftShoulderTracker; 
    public Transform rightForearmTracker; 
    public Transform leftForearmTracker; 
    public Transform rightHandTracker; 
    public Transform leftHandTracker; 

    public RawImage rawImage;
    public RawImage rawImageCamera2;
    // public Renderer renderer; // For 3D object
    public new Renderer renderer; // For 3D object


    private Texture2D texture;
    private Texture2D texture2;
    private TcpClient client;
    private NetworkStream stream;
    private string serverIp = "127.0.0.1";
    private int serverPort = 12345;

    private TcpClient imageClient;
    private NetworkStream imageStream;

    private float printDataInterval = 0.3f;
    private float printTimer = 0f;
    private float sendDataInterval = 0.3f;
    private float sendTimer = 0f;
    private float vlast = 1.0f;
    private float debugP = 1.0f;
    private float gripL = 0.0f;
    private float gripR = 0.0f;

    public bool tracking = false; 
    public bool debugPtrack = false; 
    public bool gripLtrack = false; 
    public bool gripRtrack = false; 

    private float rightStickVertical;
    private float leftStickHorizontal;

    private float leftStickVertical;

    private void Start()
    {
        ConnectToServer();
        texture = new Texture2D(2, 2);
        texture2 = new Texture2D(2, 2);
        imageClient = new TcpClient("127.0.0.1", 8089); // local pc cam
        // imageClient = new TcpClient("192.168.1.184", 8089); // other pc cam
        imageStream = imageClient.GetStream();
        StartCoroutine(ReceiveStream());
    }

    private void Update()
    {
        rightStickVertical = QuickVR.InputManager.GetAxis("FrontBack");
        leftStickHorizontal = QuickVR.InputManager.GetAxis("Turn");
        leftStickVertical = QuickVR.InputManager.GetAxis("Servo");
        Debug.Log($"Right Stick Moved to: {rightStickVertical}");
        Debug.Log($"Left Stick Moved to:{leftStickHorizontal}");
        Debug.Log($"Left Stick servo Moved to:{leftStickVertical}");
        
        
        
        if (QuickVR.InputManager.GetButtonDown("ToggledebugPtrack")){
            debugPtrack = !debugPtrack;
        }
        if (debugPtrack) {
            debugP=1;
        } else {
            debugP =0; 
        }

        if (QuickVR.InputManager.GetButton("HoldgripLtrack"))
        {
            if (!gripLtrack)
            {
                gripLtrack = true;
                gripL = 1.0f;
            }
        }
        else
        {
            if (gripLtrack)
            {
                gripLtrack = false;
                gripL = 0.0f;
            }
        }
        if (QuickVR.InputManager.GetButton("HoldgripRtrack"))
        {
            if (!gripRtrack)
            {
                gripRtrack = true;
                gripR = 1.0f;
            }
        }
        else
        {
            if (gripRtrack)
            {
                gripRtrack = false;
                gripR = 0.0f;
            }
        }

        if (QuickVR.InputManager.GetButtonDown("ToggleTracking")){
            tracking = !tracking;
        }        

        if (tracking) {
            Debug.Log("Tracking enabled!");
            Vector3 headPosition = headTracker.position;
            Quaternion headRotation = headTracker.rotation;

            Vector3 rightShoulderPosition = rightShoulderTracker.position;
            Quaternion rightShoulderRotation = rightShoulderTracker.rotation;

            Vector3 leftShoulderPosition = leftShoulderTracker.position;
            Quaternion leftShoulderRotation = leftShoulderTracker.rotation;

            Vector3 rightForearmPosition = rightForearmTracker.position;
            Quaternion rightForearmRotation = rightForearmTracker.rotation;

            Vector3 leftForearmPosition = leftForearmTracker.position;
            Quaternion leftForearmRotation = leftForearmTracker.rotation;

            Vector3 rightHandPosition = rightHandTracker.position;
            Quaternion rightHandRotation = rightHandTracker.rotation;

            Vector3 leftHandPosition = leftHandTracker.position;
            Quaternion leftHandRotation = leftHandTracker.rotation;

            printTimer += Time.deltaTime;
            sendTimer += Time.deltaTime;

            if (printTimer >= printDataInterval)
            {
                PrintValues(headPosition, headRotation, rightShoulderPosition, rightShoulderRotation, leftShoulderPosition, leftShoulderRotation, rightForearmPosition, rightForearmRotation, leftForearmPosition, leftForearmRotation, rightHandPosition, rightHandRotation, leftHandPosition, leftHandRotation);
                printTimer = 0f;
            }

            if (sendTimer >= sendDataInterval)
            {
                SendData(headPosition, headRotation, rightShoulderPosition, rightShoulderRotation, leftShoulderPosition, leftShoulderRotation, rightForearmPosition, rightForearmRotation, leftForearmPosition, leftForearmRotation, rightHandPosition, rightHandRotation, leftHandPosition, leftHandRotation);
                sendTimer = 0f;
            }
        }
    }

    IEnumerator ReceiveStream()
    {
        while (true)
        {
            yield return new WaitForEndOfFrame();

            if (imageStream.DataAvailable)
            {
                // Read the size of the incoming data
                byte[] sizeInfo = new byte[4];
                imageStream.Read(sizeInfo, 0, 4);
                int dataSize = BitConverter.ToInt32(sizeInfo, 0);

                // Read the camera index (1 byte)
                byte[] cameraIndexBuffer = new byte[1];
                imageStream.Read(cameraIndexBuffer, 0, 1);
                int cameraIndex = cameraIndexBuffer[0];
                Debug.Log($"Camera Index: {cameraIndex}"); // Debug log to check the camera index

                // Read the frame data
                byte[] data = new byte[dataSize];
                int totalBytesRead = 0;

                while (totalBytesRead < dataSize)
                {
                    int bytesRead = imageStream.Read(data, totalBytesRead, dataSize - totalBytesRead);
                    totalBytesRead += bytesRead;
                }

                // Ensure textures are unique per camera index
                if (cameraIndex == 0) // Camera 1
                {
                    texture.LoadImage(data); // Load data for camera 1
                    if (rawImage != null)
                    {
                        rawImage.texture = texture; // Assign to Camera 1's RawImage
                        Debug.Log("Assigned texture to Camera 1");
                    }
                }
                else if (cameraIndex == 1) // Camera 2
                {
                    texture2.LoadImage(data); // Load data for camera 2
                    if (rawImageCamera2 != null)
                    {
                        rawImageCamera2.texture = texture2; // Assign to Camera 2's RawImage
                        Debug.Log("Assigned texture to Camera 2");
                    }
                }
            }
        }
    }





    private void PrintValues(Vector3 headPos, Quaternion headRot, Vector3 rightShoulderPos, Quaternion rightShoulderRot, Vector3 leftShoulderPos, Quaternion leftShoulderRot, Vector3 rightForearmPos, Quaternion rightForearmRot, Vector3 leftForearmPos, Quaternion leftForearmRot, Vector3 rightHandPos, Quaternion rightHandRot, Vector3 leftHandPos, Quaternion leftHandRot)
    {
        Debug.Log($"Head Position: {headPos}, Rotation: {headRot}");
        Debug.Log($"Right Shoulder Position: {rightShoulderPos}, Rotation: {rightShoulderRot}");
        Debug.Log($"Left Shoulder Position: {leftShoulderPos}, Rotation: {leftShoulderRot}");
        Debug.Log($"Right Forearm Position: {rightForearmPos}, Rotation: {rightForearmRot}");
        Debug.Log($"Left Forearm Position: {leftForearmPos}, Rotation: {leftForearmRot}");
        Debug.Log($"Right Hand Position: {rightHandPos}, Rotation: {rightHandRot}");
        Debug.Log($"Left Hand Position: {leftHandPos}, Rotation: {leftHandRot}");
        Debug.Log($"debugP: {debugP}");
        Debug.Log($"gripL: {gripL}");
        Debug.Log($"gripR: {gripR}");
        Debug.Log($"vlast: {vlast}");
    }

    private void ConnectToServer()
    {
        try
        {
            client = new TcpClient(serverIp, serverPort);
            stream = client.GetStream();
        }
        catch (System.Exception e)
        {
            Debug.LogError($"Error connecting to server: {e.Message}");
        }
    }

    private void SendData(Vector3 headPos, Quaternion headRot, Vector3 rightShoulderPos, Quaternion rightShoulderRot, Vector3 leftShoulderPos, Quaternion leftShoulderRot, Vector3 rightForearmPos, Quaternion rightForearmRot, Vector3 leftForearmPos, Quaternion leftForearmRot, Vector3 rightHandPos, Quaternion rightHandRot, Vector3 leftHandPos, Quaternion leftHandRot)
    {
        try
        {
            string data = $"{headPos},{headRot},{rightShoulderPos},{rightShoulderRot},{leftShoulderPos},{leftShoulderRot},{rightForearmPos},{rightForearmRot},{leftForearmPos},{leftForearmRot},{rightHandPos},{rightHandRot},{leftHandPos},{leftHandRot},{debugP},{gripL},{gripR},{rightStickVertical},{leftStickHorizontal},{leftStickVertical},{vlast}\n";
            byte[] byteData = Encoding.ASCII.GetBytes(data);
            stream.Write(byteData, 0, byteData.Length);
        }
        catch (System.Exception e)
        {
            Debug.LogError($"Error sending data to server: {e.Message}");
        }
    }

    private void OnDestroy()
    {
        if (client != null)
        {
            client.Close();
        }
        if (imageClient != null)
        {
            imageStream.Close();
            imageClient.Close();
        }
    }
}
