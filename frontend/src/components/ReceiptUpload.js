import { useEffect, useRef, useState } from "react";
import Navbar from "./Navbar";
import {
    cancelReceiptPreview,
    confirmReceiptUpload,
    extractReceiptPreview,
} from "../services/apiService";
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
    const [previewData, setPreviewData] = useState(null);
    const [loadingLabel, setLoadingLabel] = useState("Processing your receipt...");
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
        setPreviewData(null);
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
        setPreviewData(null);

        const objectUrl = URL.createObjectURL(file);
        setPreview(objectUrl);
    };

    const handleFileChange = (event) => {
        handleFileSelection(event.target.files[0]);
    };

    const handleDrop = (event) => {
        event.preventDefault();
        setIsDragging(false);
        handleFileSelection(event.dataTransfer.files[0]);
    };

    const handleExtractPreview = async () => {
        if (!selectedFile) {
            setMessage("Please select a receipt.");
            setMessageType("error");
            return;
        }

        setLoading(true);
        setUploadProgress(10);
        setLoadingLabel("Extracting receipt details...");
        setMessage("Extracting receipt details...");
        setMessageType("info");

        try {
            const data = await extractReceiptPreview(selectedFile, user?.user_id || "1");
            setUploadProgress(100);

            const parsedData = data?.data || {};
            setPreviewData({
                merchantName: parsedData.merchant_name || "Not available",
                receiptDate: parsedData.receipt_date || "Not available",
                totalAmount: parsedData.total_amount ?? "",
                currency: parsedData.currency || "Not available",
                category: parsedData.category || "Not available",
                tempFilePath: parsedData.temp_file_path,
            });
            setExtractedData(null);
            setMessage("Please verify the extracted receipt details before uploading.");
            setMessageType("info");
        } catch (err) {
            setPreviewData(null);
            setExtractedData(null);
            setMessage(err.message || "Unable to connect to the server.");
            setMessageType("error");
        } finally {
            setLoading(false);
        }
    };

    const handleConfirmUpload = async () => {
        if (!previewData?.tempFilePath) {
            setMessage("Receipt preview is missing. Please extract again.");
            setMessageType("error");
            return;
        }

        setLoading(true);
        setLoadingLabel("Saving receipt...");
        setMessage("Saving receipt...");
        setMessageType("info");

        try {
            const data = await confirmReceiptUpload({
                user_id: user?.user_id || "1",
                temp_file_path: previewData.tempFilePath,
                merchant_name: previewData.merchantName,
                receipt_date: previewData.receiptDate,
                total_amount: previewData.totalAmount,
                currency: previewData.currency,
                category: previewData.category,
            });

            const parsedData = data?.data || {};
            setExtractedData({
                merchantName: parsedData.merchant_name || "Not available",
                receiptDate: parsedData.receipt_date || "Not available",
                totalAmount: parsedData.total_amount ?? "Not available",
                currency: parsedData.currency || "Not available",
                category: parsedData.category || "Not available",
            });
            setPreviewData(null);
            setMessage("Receipt uploaded successfully!");
            setMessageType("success");
        } catch (err) {
            setMessage(err.message || "Unable to connect to the server.");
            setMessageType("error");
        } finally {
            setLoading(false);
        }
    };

    const handleCancelPreview = async () => {
        if (previewData?.tempFilePath) {
            try {
                await cancelReceiptPreview(previewData.tempFilePath);
            } catch {
                // Continue with local reset to keep the UI responsive even if cancellation cleanup fails.
            }
        }

        resetUpload();
        setMessage("Receipt upload cancelled.");
        setMessageType("info");
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
                        accept=".jpg,.jpeg,.png,.webp"
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
                        <span>{loadingLabel}</span>
                        <div className="progress-bar">
                            <div className="progress-fill" style={{ width: `${uploadProgress}%` }} />
                        </div>
                    </div>
                )}

                <div className="actions-row">
                    {!previewData ? (
                        <>
                            <button
                                onClick={handleExtractPreview}
                                disabled={loading || !selectedFile}
                                className="upload-button"
                            >
                                {loading ? "Extracting..." : "Extract Details"}
                            </button>

                            <button
                                type="button"
                                onClick={resetUpload}
                                className="reset-button"
                                disabled={loading}
                            >
                                Reset
                            </button>
                        </>
                    ) : (
                        <>
                            <button
                                type="button"
                                onClick={handleConfirmUpload}
                                disabled={loading}
                                className="upload-button"
                            >
                                {loading ? "Confirming..." : "Confirm Upload"}
                            </button>

                            <button
                                type="button"
                                onClick={handleCancelPreview}
                                className="reset-button"
                                disabled={loading}
                            >
                                Cancel
                            </button>
                        </>
                    )}
                </div>

                {previewData && (
                    <div className="result-card" aria-live="polite">
                        <div className="result-card-header">
                            <h3>Review receipt details</h3>
                            <span>Please verify before uploading</span>
                        </div>
                        <p className="preview-helper-text">Please verify the extracted receipt details before uploading.</p>

                        <div className="result-grid">
                            <div className="result-item">
                                <p className="result-label">Merchant Name</p>
                                <input
                                    type="text"
                                    className="result-input"
                                    value={previewData.merchantName}
                                    onChange={(event) => setPreviewData((current) => ({ ...current, merchantName: event.target.value }))}
                                />
                            </div>

                            <div className="result-item">
                                <p className="result-label">Receipt Date</p>
                                <input
                                    type="date"
                                    className="result-input"
                                    value={previewData.receiptDate}
                                    onChange={(event) => setPreviewData((current) => ({ ...current, receiptDate: event.target.value }))}
                                />
                            </div>

                            <div className="result-item">
                                <p className="result-label">Total Amount</p>
                                <input
                                    type="number"
                                    className="result-input"
                                    value={previewData.totalAmount}
                                    step="0.01"
                                    onChange={(event) => setPreviewData((current) => ({ ...current, totalAmount: event.target.value }))}
                                />
                            </div>

                            <div className="result-item">
                                <p className="result-label">Currency</p>
                                <input
                                    type="text"
                                    className="result-input"
                                    value={previewData.currency}
                                    onChange={(event) => setPreviewData((current) => ({ ...current, currency: event.target.value.toUpperCase() }))}
                                />
                            </div>

                            <div className="result-item">
                                <p className="result-label">Expense Category</p>
                                <input
                                    type="text"
                                    className="result-input"
                                    value={previewData.category}
                                    onChange={(event) => setPreviewData((current) => ({ ...current, category: event.target.value }))}
                                />
                            </div>
                        </div>
                    </div>
                )}

                {extractedData && !previewData && (
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