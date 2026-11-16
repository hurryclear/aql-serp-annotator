import { Routes, Route } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import AnnotationPage from "./pages/AnnotationPage";
import EditorHomePage from "./pages/EditorHomePage";
import EditorPage from "./pages/EditorPage";
import ParserPage from "./pages/ParserPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/workspace" element={<AnnotationPage />} />
      <Route path="/editor" element={<EditorHomePage />} />
      <Route path="/editor/:providerId/:year" element={<EditorPage />} />
      <Route path="/parsers/:providerId/:year" element={<ParserPage />} />
    </Routes>
  );
}

export default App;
