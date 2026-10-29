import type { ReactNode } from "react";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";

// the single centred card the landing page, "all done" and "not open" screens share
function CenteredCard({ children }: { children: ReactNode }) {
  return (
    <Box sx={{ minHeight: "100%", display: "flex", alignItems: "center", justifyContent: "center", p: 2 }}>
      <Card sx={{ width: "100%", maxWidth: 380 }}>
        <CardContent sx={{ p: 3 }}>{children}</CardContent>
      </Card>
    </Box>
  );
}

export default CenteredCard;
