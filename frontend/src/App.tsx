import { Routes, Route } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import AnnotationPage from "./pages/AnnotationPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/workspace/:cartId" element={<AnnotationPage />} />
    </Routes>
  );
}

export default App;
