import { BrowserRouter, Routes, Route } from "react-router-dom";

import Home from "./pages/Home";
import Summary from "./pages/Summary";
import ReceiptUpload from "./components/ReceiptUpload";

function App() {
    return (
        <BrowserRouter>
            <Routes>

                <Route
                    path="/"
                    element={<Home />}
                />

                <Route
                    path="/upload"
                    element={<ReceiptUpload />}
                />

                <Route
                    path="/summary"
                    element={<Summary />}
                />

            </Routes>
        </BrowserRouter>
    );
}

export default App;