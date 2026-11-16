import { useState } from "react";
import Link from "@mui/material/Link";
import Typography from "@mui/material/Typography";
import { Link as RouterLink } from "react-router-dom";
import CenteredCard from "../components/CenteredCard";
import AnnotateForm from "../components/home/AnnotateForm";
import type { CartForm } from "../components/home/landingForm";

const EMPTY_FORM: CartForm = { provider: "", language: "", year: "", createdBy: "" };

function LandingPage() {
  const [form, setForm] = useState<CartForm>(EMPTY_FORM);
  return (
    <CenteredCard>
      <AnnotateForm form={form} onFormChange={setForm} />
      <Typography variant="body2" sx={{ mt: 2, textAlign: "center" }}>
        <Link component={RouterLink} to="/editor">Review or edit saved annotations</Link>
      </Typography>
    </CenteredCard>
  );
}

export default LandingPage;
