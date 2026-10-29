import { useRef } from "react";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import Typography from "@mui/material/Typography";

type SerpFrameProps = {
  html: string | null;
  error: string | null;
  onReady: (doc: Document) => void;
};

// srcDoc, not src: a srcdoc iframe shares this page's origin, so the page can read
// the block the annotator marked in DevTools. A src on :8000 would be cross-origin.
function SerpFrame({ html, error, onReady }: SerpFrameProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  function handleLoad() {
    const doc = iframeRef.current?.contentDocument;
    if (doc) onReady(doc);
  }

  return (
    <Card sx={{ flex: 1, minWidth: 0, display: "flex" }}>
      {error ? (
        <Typography color="error" sx={{ m: "auto", p: 2 }}>{error}</Typography>
      ) : html === null ? (
        <Typography color="text.secondary" sx={{ m: "auto" }}>Loading SERP…</Typography>
      ) : (
        <Box
          component="iframe"
          ref={iframeRef}
          title="SERP"
          srcDoc={html}
          onLoad={handleLoad}
          sx={{ flex: 1, border: 0, width: "100%", height: "100%", bgcolor: "#fff" }}
        />
      )}
    </Card>
  );
}

export default SerpFrame;
