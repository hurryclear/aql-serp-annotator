import { useState } from "react";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import AnnotateForm from "../components/home/AnnotateForm";
import AnnotationGroups from "../components/home/AnnotationGroups";
import type { CartForm } from "../components/home/landingForm";

const EMPTY_FORM: CartForm = { provider: "", language: "", year: "", createdBy: "" };

// the start page: choose SERPs to annotate on the left, the saved annotations on the right.
// The form lives here, not in AnnotateForm, because the table also reads its provider and year.
function HomePage() {
  const [form, setForm] = useState<CartForm>(EMPTY_FORM);

  return (
    // side by side; on a narrow window the table wraps below the form
    <Box sx={{ minHeight: "100%", display: "flex", flexWrap: "wrap", justifyContent: "center", alignItems: "flex-start", gap: 2, p: 2, pt: 6 }}>
      <Card sx={{ width: "100%", maxWidth: 380 }}>
        <CardContent sx={{ p: 3 }}>
          <AnnotateForm form={form} onFormChange={setForm} />
        </CardContent>
      </Card>
      {/* 640px is about what the table needs; below that it wraps instead of scrolling sideways */}
      <Card sx={{ flex: "1 1 640px", maxWidth: 820, minWidth: 0 }}>
        <CardContent sx={{ p: 3, overflowX: "auto" }}>
          <AnnotationGroups provider={form.provider} year={form.year} />
        </CardContent>
      </Card>
    </Box>
  );
}

export default HomePage;
