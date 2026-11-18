import { useState } from "react";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import AnnotateForm from "../components/home/AnnotateForm";
import AnnotationGroups from "../components/home/AnnotationGroups";
import ParserGroups from "../components/home/ParserGroups";
import type { CartForm } from "../components/home/landingForm";

const EMPTY_FORM: CartForm = { provider: "", language: "", year: "", createdBy: "" };

// the start page: choose SERPs to annotate on the left, the saved annotations on the right.
// The form lives here, not in AnnotateForm, because the table also reads its provider and year.
function HomePage() {
  const [form, setForm] = useState<CartForm>(EMPTY_FORM);

  return (
    // side by side and centred on the page; "stretch" makes both cards as tall as the taller one.
    // On a narrow window the table wraps below the form (alignContent centres the wrapped rows).
    <Box sx={{ minHeight: "100%", display: "flex", flexWrap: "wrap", justifyContent: "center", alignContent: "center", alignItems: "stretch", gap: 2, p: 2 }}>
      <Card sx={{ width: "100%", maxWidth: 380 }}>
        <CardContent sx={{ p: 3 }}>
          <AnnotateForm form={form} onFormChange={setForm} />
        </CardContent>
      </Card>
      {/* 640px is about what the tables need; below that the column wraps instead of scrolling sideways.
          The parser card sits right under the saved annotations, in the same column */}
      <Box sx={{ flex: "1 1 640px", maxWidth: 820, minWidth: 0, display: "flex", flexDirection: "column", gap: 2 }}>
        <Card>
          <CardContent sx={{ p: 3, overflowX: "auto" }}>
            <AnnotationGroups provider={form.provider} year={form.year} />
          </CardContent>
        </Card>
        <Card>
          <CardContent sx={{ p: 3, overflowX: "auto" }}>
            <ParserGroups provider={form.provider} />
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
}

export default HomePage;
