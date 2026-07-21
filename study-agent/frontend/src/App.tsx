import { Route, Routes } from "react-router-dom";
import { PrivacyBanner } from "./components/PrivacyBanner";
import { NavBar } from "./components/NavBar";
import { UploadPage } from "./pages/UploadPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { ReviewPage } from "./pages/ReviewPage";
import { SettingsPage } from "./pages/SettingsPage";
import { GraphPage } from "./pages/GraphPage";
import { SchedulePage } from "./pages/SchedulePage";
import { PlaceholderPage } from "./pages/PlaceholderPage";

export default function App() {
  return (
    <div className="app-shell">
      <PrivacyBanner />
      <header className="app-header">
        <h1 className="app-title">Study Agent</h1>
        <NavBar />
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/documents/:id/review" element={<ReviewPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/graph" element={<GraphPage />} />
          <Route path="/schedule" element={<SchedulePage />} />
          <Route
            path="/export"
            element={
              <PlaceholderPage
                title="Export center"
                note="Coming in Module 5: notes, graph, flashcards, and schedule export bundle."
              />
            }
          />
        </Routes>
      </main>
    </div>
  );
}
