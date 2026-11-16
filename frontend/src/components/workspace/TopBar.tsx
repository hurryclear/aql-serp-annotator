import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import LinearProgress from "@mui/material/LinearProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

type TopBarProps = {
  position: number; // 1-based
  total: number;
  serpId: string;
  provider: string;
  language?: string; // the editor groups by provider and year only
  year: number;
  onExit: () => void;
  exitLabel?: string;
  // the editor moves back and forth; the annotation page only moves on
  onPrev?: () => void;
  onNext?: () => void;
};

function TopBar({ position, total, serpId, provider, language, year, onExit, exitLabel = "Exit", onPrev, onNext }: TopBarProps) {
  return (
    <Card sx={{ borderRadius: 1 }}>
      <Stack direction="row" spacing={1.5} sx={{ alignItems: "center", px: 1.5, py: 1 }}>
        <Typography variant="subtitle1" sx={{ whiteSpace: "nowrap" }}>
          SERP {position} of {total}
        </Typography>
        {/* selectable, so it can be copied to look the SERP up elsewhere */}
        <Typography variant="caption" color="text.secondary" sx={{ fontFamily: "monospace", whiteSpace: "nowrap", userSelect: "all" }}>
          {serpId}
        </Typography>
        <LinearProgress variant="determinate" value={(position / total) * 100} sx={{ flex: 1 }} />
        <Typography variant="caption" color="text.secondary" sx={{ whiteSpace: "nowrap" }}>
          {language ? `${provider} · ${language} · ${year}` : `${provider} · ${year}`}
        </Typography>
        {onPrev && <Button variant="outlined" size="small" onClick={onPrev} disabled={position <= 1}>Previous</Button>}
        {onNext && <Button variant="outlined" size="small" onClick={onNext} disabled={position >= total}>Next</Button>}
        <Button variant="outlined" size="small" onClick={onExit} sx={{ whiteSpace: "nowrap" }}>{exitLabel}</Button>
      </Stack>
    </Card>
  );
}

export default TopBar;
