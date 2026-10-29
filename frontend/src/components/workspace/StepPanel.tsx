import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import IconButton from "@mui/material/IconButton";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { alpha } from "@mui/material/styles";
import CloseIcon from "@mui/icons-material/Close";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import Kbd from "./Kbd";
import type { AcceptedBlock, FeatureType } from "../../types/workspace";

const MARK_COMMAND = "$0.classList.add('fb-testing')";

type StepPanelProps = {
  blockNumber: number;
  featureTypes: FeatureType[];
  selectedType: string | null;
  onSelectType: (id: string) => void;
  onAccept: () => void;
  accepted: AcceptedBlock[];
  onRemove: (index: number) => void;
  onSave: () => void;
  onNoBlocks: () => void;
  onSkip: () => void;
  message: string | null;
  busy: boolean;
};

function StepTitle({ children }: { children: string }) {
  return <Typography variant="subtitle2" sx={{ mb: 1 }}>{children}</Typography>;
}

function StepPanel(props: StepPanelProps) {
  const { blockNumber, featureTypes, selectedType, onSelectType, onAccept, accepted, onRemove, onSave, onNoBlocks, onSkip, message, busy } = props;

  return (
    <Card sx={{ width: 360, flexShrink: 0, display: "flex", flexDirection: "column" }}>
      {/* the steps scroll on their own; the save buttons below always stay visible */}
      <Stack spacing={2.5} sx={{ p: 2, overflowY: "auto", flex: 1 }}>
        <Typography variant="h6" component="h2">Feature block #{blockNumber}</Typography>

        <Box>
          <StepTitle>1. Mark it in DevTools</StepTitle>
          <Stack direction="row" sx={{ alignItems: "center", bgcolor: "action.hover", borderRadius: 1, pl: 1 }}>
            <Typography component="code" sx={{ flex: 1, fontFamily: "monospace", fontSize: 12 }}>{MARK_COMMAND}</Typography>
            <IconButton size="small" aria-label="Copy command" onClick={() => navigator.clipboard.writeText(MARK_COMMAND)}>
              <ContentCopyIcon fontSize="small" />
            </IconButton>
          </Stack>
        </Box>

        <Box>
          <StepTitle>2. Choose a category</StepTitle>
          <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 0.75 }}>
            {featureTypes.map((type) => {
              const selected = type.id === selectedType;
              return (
                <Button
                  key={type.id}
                  variant="outlined"
                  size="small"
                  color={selected ? "primary" : "inherit"}
                  onClick={() => onSelectType(type.id)}
                  sx={{
                    justifyContent: "flex-start",
                    textAlign: "left",
                    lineHeight: 1.3,
                    borderColor: selected ? undefined : "divider",
                    bgcolor: selected ? (theme) => alpha(theme.palette.primary.main, 0.08) : undefined,
                  }}
                >
                  {type.label}
                </Button>
              );
            })}
          </Box>
        </Box>

        <Button variant="outlined" fullWidth onClick={onAccept} disabled={busy}>
          Accept block<Kbd>2</Kbd>
        </Button>

        <Box>
          <StepTitle>{`Accepted on this SERP (${accepted.length})`}</StepTitle>
          {accepted.map((block) => (
            <Stack key={block.index} direction="row" sx={{ alignItems: "center", py: 0.25 }}>
              <Typography variant="body2" color="text.secondary" sx={{ flex: 1 }}>
                #{block.index} {block.label}
              </Typography>
              <IconButton size="small" aria-label="Remove" onClick={() => onRemove(block.index)} disabled={busy}>
                <CloseIcon fontSize="small" />
              </IconButton>
            </Stack>
          ))}
        </Box>
      </Stack>

      <Stack spacing={1} sx={{ p: 2, borderTop: 1, borderColor: "divider" }}>
        {message && <Typography variant="body2" color="error">{message}</Typography>}
        <Button variant="contained" fullWidth onClick={onSave} disabled={busy}>
          Save and next<Kbd>3</Kbd>
        </Button>
        <Stack direction="row" spacing={1}>
          <Button variant="outlined" fullWidth onClick={onNoBlocks} disabled={busy}>
            No blocks<Kbd>4</Kbd>
          </Button>
          <Button variant="outlined" fullWidth onClick={onSkip} disabled={busy}>
            Skip<Kbd>1</Kbd>
          </Button>
        </Stack>
      </Stack>
    </Card>
  );
}

export default StepPanel;
