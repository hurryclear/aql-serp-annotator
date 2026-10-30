import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import CenteredCard from "../CenteredCard";

function DoneCard({ total, onBack }: { total: number; onBack: () => void }) {
  return (
    <CenteredCard>
      <Typography variant="h5" component="h1">All {total} done</Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mt: 0.5, mb: 2.5 }}>
        Every SERP in this cart is saved or skipped.
      </Typography>
      <Button variant="outlined" fullWidth onClick={onBack}>Back to start</Button>
    </CenteredCard>
  );
}

export default DoneCard;
