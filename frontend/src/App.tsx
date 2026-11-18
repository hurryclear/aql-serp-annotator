import { Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import AnnotationPage from "./pages/AnnotationPage";
import EditorPage from "./pages/EditorPage";
import ParserPage from "./pages/ParserPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/workspace" element={<AnnotationPage />} />
      <Route path="/editor/:providerId/:year" element={<EditorPage />} />
      <Route path="/parsers/:providerId/:year" element={<ParserPage />} />
      {/* the start page's Parsers card: one feature type, SERPs of every year */}
      <Route path="/parsers/:providerId/type/:featureType" element={<ParserPage />} />
    </Routes>
  );
}

export default App;
