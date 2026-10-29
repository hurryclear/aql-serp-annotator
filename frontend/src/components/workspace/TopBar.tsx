import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import LinearProgress from "@mui/material/LinearProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

type TopBarProps = {
  position: number; // 1-based
  total: number;
  provider: string;
  language: string;
  year: number;
  onExit: () => void;
};

function TopBar({ position, total, provider, language, year, onExit }: TopBarProps) {
  return (
    <Card>
      <Stack direction="row" spacing={2} sx={{ alignItems: "center", px: 2, py: 1 }}>
        <Typography variant="subtitle2" sx={{ whiteSpace: "nowrap" }}>
          SERP {position} of {total}
        </Typography>
        <LinearProgress variant="determinate" value={(position / total) * 100} sx={{ flex: 1, height: 6, borderRadius: 3 }} />
        <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: "nowrap" }}>
          {provider} · {language} · {year}
        </Typography>
        <Button variant="outlined" size="small" onClick={onExit}>Exit</Button>
      </Stack>
    </Card>
  );
}

export default TopBar;
