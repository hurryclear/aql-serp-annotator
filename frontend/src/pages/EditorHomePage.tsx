import { Link as RouterLink } from "react-router-dom";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Link from "@mui/material/Link";
import Typography from "@mui/material/Typography";
import AnnotationGroups from "../components/home/AnnotationGroups";

// the editor's start: every annotation, grouped by provider and year
function EditorHomePage() {
  return (
    <Box sx={{ minHeight: "100%", display: "flex", justifyContent: "center", alignItems: "flex-start", p: 2 }}>
      <Card sx={{ width: "100%", maxWidth: 760, mt: 6 }}>
        <CardContent sx={{ p: 3 }}>
          <AnnotationGroups provider="" year="" />
          <Typography variant="body2" sx={{ mt: 2 }}>
            <Link component={RouterLink} to="/">Back to annotating</Link>
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}

export default EditorHomePage;
