import React, { useState } from "react";
import "./ReceiptUpload.css";

function ReceiptUpload() {
    const [selectedFile, setSelectedFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [message, setMessage] = useState("");
    const [loading, setLoading] = useState(false);

    const handleFileChange = (event) => {
        const file = event.target.files[0];

        if (!file) return;

        const allowedTypes = [
            "image/jpeg",
            "image/png",
            "application/pdf",
        ];

        if (!allowedTypes.includes(file.type)) {
            setMessage("Please upload a JPG, PNG or PDF receipt.");
            return;
        }

        setSelectedFile(file);
        setMessage("");

        if (file.type !== "application/pdf") {
            setPreview(URL.createObjectURL(file));
        } else {
            setPreview(null);
        }
    };

    const handleUpload = async () => {

        if (!selectedFile) {
            setMessage("Please select a receipt.");
            return;
        }

        const formData = new FormData();

        formData.append("file", selectedFile);
        formData.append("user_id", "1"); // Replace with the logged-in user's ID later

        try {

            const response = await fetch(
                "http://localhost:5000/api/upload",
                {
                    method: "POST",
                    body: formData,
                }
            );

            const data = await response.json();

            console.log(data);

            if (response.ok) {
                setMessage("Receipt uploaded successfully!");
            } else {
                setMessage(data.error);
            }

        } catch (err) {
            console.error(err);
            setMessage("Unable to connect to server.");
        }
    };

    return (
        <div className="receipt-container">

            <h2>Upload Receipt</h2>

            <input
                type="file"
                accept=".jpg,.jpeg,.png,.pdf"
                onChange={handleFileChange}
                className="file-input"
            />

            {preview && (
                <img
                    src={preview}
                    alt="Receipt Preview"
                    className="receipt-preview"
                />
            )}

            {selectedFile &&
                selectedFile.type === "application/pdf" && (
                    <div className="pdf-preview">
                        📄 {selectedFile.name}
                    </div>
                )}

            <button
                onClick={handleUpload}
                disabled={loading}
                className="upload-button"
            >
                {loading ? "Uploading..." : "Upload Receipt"}
            </button>

            {message && (
                <p className="message">{message}</p>
            )}

        </div>
    );
}

export default ReceiptUpload;