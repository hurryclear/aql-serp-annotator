import { useState } from "react";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import TextField from "@mui/material/TextField";
import Stack from "@mui/material/Stack";
import Button from "@mui/material/Button";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import { useNavigate } from "react-router-dom";
import { createCart } from "../api/carts";
import Selector from "../components/Selector";
import { missingFields, type CartForm } from "./landingForm";
import type { WorkspaceState } from "../types/workspace";

const PROVIDERS = ["Google", "Baidu", "Bing", "DuckDuckGo", "Yandex", "Twitter", "Wikipedia", "YouTube", "Google Scholar", "SemanticScholar", "e621", "360", "Weibo"];
const LANGUAGES = ["Arabic", "Bengali", "German", "English", "Spanish", "French", "Indonesian", "Portuguese", "Russian", "Chinese"];
const YEARS = ["2010", "2011", "2012", "2013"];

const EMPTY_FORM: CartForm = { provider: "", language: "", year: "", createdBy: "" };

function LandingPage() {
  const [form, setForm] = useState<CartForm>(EMPTY_FORM);
  const [missing, setMissing] = useState<(keyof CartForm)[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  // editing a field clears its red outline and any message under the button
  function update(field: keyof CartForm, value: string) {
    setForm({ ...form, [field]: value });
    setMissing(missing.filter((f) => f !== field));
    setError(null);
  }

  async function handleSubmit() {
    const empty = missingFields(form);
    if (empty.length > 0) {
      setMissing(empty);
      return;
    }
    setBusy(true);
    try {
      const year = Number(form.year);
      const result = await createCart({
        provider: form.provider,
        language: form.language,
        year,
        created_by: form.createdBy.trim(),
        batch_size: 25,
      });
      if (result.id == null) {
        setError("No SERPs match these choices. Try a different year.");
        return;
      }
      // the SERP ids only live in the browser (ADR 0005), so they travel with the navigation
      const state: WorkspaceState = { serpIds: result.serp_ids, provider: form.provider, language: form.language, year };
      navigate(`/workspace/${result.id}`, { state });
    } catch {
      setError("Couldn't create a cart. Check that the backend is running, then try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Box sx={{ minHeight: "100%", display: "flex", alignItems: "center", justifyContent: "center", p: 2 }}>
      <Card sx={{ width: "100%", maxWidth: 380 }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h5" component="h1">AQL SERP annotation</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, mb: 3 }}>
            Choose which SERPs to annotate in this sitting.
          </Typography>
          <Stack spacing={2}>
            <Selector label="Provider" options={PROVIDERS} value={form.provider} onChange={(v) => update("provider", v)} error={missing.includes("provider")} />
            <Selector label="Language" options={LANGUAGES} value={form.language} onChange={(v) => update("language", v)} error={missing.includes("language")} />
            <Selector label="Year" options={YEARS} value={form.year} onChange={(v) => update("year", v)} error={missing.includes("year")} />
            <TextField
              label="Your name"
              variant="standard"
              value={form.createdBy}
              onChange={(e) => update("createdBy", e.target.value)}
              error={missing.includes("createdBy")}
            />
          </Stack>
          <Typography variant="caption" color="text.secondary" component="p" sx={{ mt: 2 }}>
            You'll get up to 25 SERPs you haven't annotated yet.
          </Typography>
          <Button
            variant="contained"
            fullWidth
            endIcon={<ArrowForwardIcon />}
            onClick={handleSubmit}
            disabled={busy}
            sx={{ mt: 1.5 }}
          >
            Start annotating
          </Button>
          {error && (
            <Typography variant="body2" color="error" sx={{ mt: 1.5 }}>
              {error}
            </Typography>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}

export default LandingPage;
