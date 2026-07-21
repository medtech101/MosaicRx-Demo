import { Route, Routes } from "react-router-dom";
import { PrivacyBanner } from "./components/PrivacyBanner";
import { NavBar } from "./components/NavBar";
import { UploadPage } from "./pages/UploadPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { ReviewPage } from "./pages/ReviewPage";
import { SettingsPage } from "./pages/SettingsPage";
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
          <Route
            path="/graph"
            element={
              <PlaceholderPage
                title="Knowledge graph"
                note="Coming in Module 2: bridge concepts, clusters, and the force-directed concept graph."
              />
            }
          />
          <Route
            path="/schedule"
            element={
              <PlaceholderPage
                title="Study schedule"
                note="Coming in Module 4: spaced-repetition weekly plan and ICS export."
              />
            }
          />
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
