import { useEffect, useRef, useState } from "react";
import Navbar from "./Navbar";
import { uploadReceipt } from "../services/apiService";
import { saveRecentReceipt } from "../services/dashboardService";
import "./ReceiptUpload.css";

function ReceiptUpload({ user, onLogout }) {
    const [selectedFile, setSelectedFile] = useState(null);
    const [preview, setPreview] = useState(null);
    const [message, setMessage] = useState("");
    const [messageType, setMessageType] = useState("info");
    const [loading, setLoading] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [isDragging, setIsDragging] = useState(false);
    const [extractedData, setExtractedData] = useState(null);
    const fileInputRef = useRef(null);

    useEffect(() => {
        return () => {
            if (preview) {
                URL.revokeObjectURL(preview);
            }
        };
    }, [preview]);

    const resetUpload = () => {
        if (preview) {
            URL.revokeObjectURL(preview);
        }
        setSelectedFile(null);
        setPreview(null);
        setMessage("");
        setMessageType("info");
        setUploadProgress(0);
        setExtractedData(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    const handleFileSelection = (file) => {
        if (!file) return;

        const allowedTypes = [
            "image/jpeg",
            "image/png",
            "image/webp",
        ];

        if (!allowedTypes.includes(file.type)) {
            setMessage("Please upload a clear JPG, PNG, or WebP receipt image.");
            setMessageType("error");
            return;
        }

        setSelectedFile(file);
        setMessage("");
        setMessageType("info");
        setUploadProgress(0);
        setExtractedData(null);

        if (file.type !== "application/pdf") {
            const objectUrl = URL.createObjectURL(file);
            setPreview(objectUrl);
        } else {
            setPreview(null);
        }
    };

    const handleFileChange = (event) => {
        handleFileSelection(event.target.files[0]);
    };

    const handleDrop = (event) => {
        event.preventDefault();
        setIsDragging(false);
        handleFileSelection(event.dataTransfer.files[0]);
    };

    const handleUpload = async () => {
        if (!selectedFile) {
            setMessage("Please select a receipt.");
            setMessageType("error");
            return;
        }

        setLoading(true);
        setUploadProgress(10);
        setMessage("Uploading receipt...");
        setMessageType("info");

        try {
            const data = await uploadReceipt(selectedFile, user?.user_id || "1");
            setUploadProgress(100);

            const parsedData = data?.data || {};
            const receiptSummary = {
                id: parsedData.receipt_id || `${selectedFile.name}-${Date.now()}`,
                merchant: parsedData.merchant_name || "Not available",
                category: parsedData.category || "Uncategorized",
                amount: Number(parsedData.total_amount || 0),
                currency: parsedData.currency || "USD",
                amountInSgd: parsedData.amount_in_sgd ?? null,
                date: parsedData.receipt_date || new Date().toISOString().slice(0, 10),
            };

            saveRecentReceipt(receiptSummary);
            setExtractedData({
                merchantName: parsedData.merchant_name || "Not available",
                receiptDate: parsedData.receipt_date || "Not available",
                totalAmount: parsedData.total_amount ?? "Not available",
                currency: parsedData.currency || "Not available",
                category: parsedData.category || "Not available",
            });
            setMessage("Receipt uploaded successfully!");
            setMessageType("success");
        } catch (err) {
            setExtractedData(null);
            setMessage(err.message || "Unable to connect to the server.");
            setMessageType("error");
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <Navbar user={user} onLogout={onLogout} />

            <main id="main-content" className="receipt-container">
                <div className="receipt-header">
                    <div>
                        <h2>Upload Receipt</h2>
                        <p>Upload a receipt and let the AI extract the details.</p>
                    </div>
                </div>

                <div
                    className={`dropzone ${isDragging ? "dropzone-active" : ""}`}
                    onDragOver={(event) => {
                        event.preventDefault();
                        setIsDragging(true);
                    }}
                    onDragLeave={() => setIsDragging(false)}
                    onDrop={handleDrop}
                >
                    <p className="dropzone-title">Drag and drop your receipt here</p>
                    <p className="dropzone-subtitle">JPG, PNG, or WebP images</p>

                    <button
                        type="button"
                        className="browse-button"
                        onClick={() => fileInputRef.current?.click()}
                    >
                        Browse files
                    </button>

                    <label htmlFor="receipt-file" className="sr-only">
                        Choose receipt file
                    </label>
                    <input
                        id="receipt-file"
                        ref={fileInputRef}
                        type="file"
                        accept=".jpg,.jpeg,.png,.pdf"
                        onChange={handleFileChange}
                        className="file-input"
                        aria-label="Choose a receipt file"
                    />
                </div>

                {selectedFile && (
                    <div className="selected-file-card">
                        <div className="selected-file-meta">
                            <strong>{selectedFile.name}</strong>
                            <span>{(selectedFile.size / 1024).toFixed(1)} KB</span>
                        </div>

                        {preview ? (
                            <img
                                src={preview}
                                alt="Receipt Preview"
                                className="receipt-preview"
                            />
                        ) : (
                            <div className="pdf-preview">📄 {selectedFile.name}</div>
                        )}
                    </div>
                )}

                {loading && (
                    <div className="progress-card" aria-live="polite">
                        <div className="spinner" />
                        <span>Processing your receipt...</span>
                        <div className="progress-bar">
                            <div className="progress-fill" style={{ width: `${uploadProgress}%` }} />
                        </div>
                    </div>
                )}

                <div className="actions-row">
                    <button
                        onClick={handleUpload}
                        disabled={loading || !selectedFile}
                        className="upload-button"
                    >
                        {loading ? "Uploading..." : "Upload Receipt"}
                    </button>

                    <button
                        type="button"
                        onClick={resetUpload}
                        className="reset-button"
                        disabled={loading}
                    >
                        Reset
                    </button>
                </div>

                {extractedData && (
                    <div className="result-card" aria-live="polite">
                        <div className="result-card-header">
                            <h3>Extracted receipt details</h3>
                            <span>AI summary</span>
                        </div>

                        <div className="result-grid">
                            <div className="result-item">
                                <p className="result-label">Merchant Name</p>
                                <p className="result-value">{extractedData.merchantName}</p>
                            </div>

                            <div className="result-item">
                                <p className="result-label">Receipt Date</p>
                                <p className="result-value">{extractedData.receiptDate}</p>
                            </div>

                            <div className="result-item">
                                <p className="result-label">Total Amount</p>
                                <p className="result-value">
                                    {typeof extractedData.totalAmount === "number"
                                        ? `$${extractedData.totalAmount.toFixed(2)}`
                                        : extractedData.totalAmount}
                                </p>
                            </div>

                            <div className="result-item">
                                <p className="result-label">Currency</p>
                                <p className="result-value">{extractedData.currency}</p>
                            </div>

                            <div className="result-item">
                                <p className="result-label">Expense Category</p>
                                <p className="result-value">{extractedData.category}</p>
                            </div>
                        </div>
                    </div>
                )}

                {message && (
                    <p className={`message ${messageType}`}>{message}</p>
                )}
            </main>
        </>
    );
}

export default ReceiptUpload;