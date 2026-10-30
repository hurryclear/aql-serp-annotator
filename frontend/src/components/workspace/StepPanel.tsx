import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import IconButton from "@mui/material/IconButton";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import CloseIcon from "@mui/icons-material/Close";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import Kbd from "./Kbd";
import InlineError from "../InlineError";
import { tokens } from "../../theme";
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
  return <Typography variant="subtitle2" sx={{ mb: 0.75 }}>{children}</Typography>;
}

function StepPanel(props: StepPanelProps) {
  const { blockNumber, featureTypes, selectedType, onSelectType, onAccept, accepted, onRemove, onSave, onNoBlocks, onSkip, message, busy } = props;

  return (
    <Card sx={{ width: 300, flexShrink: 0, display: "flex", flexDirection: "column", borderRadius: 1 }}>
      {/* the steps scroll on their own; the save buttons below always stay visible */}
      <Stack spacing={1.75} sx={{ p: 1.5, overflowY: "auto", flex: 1 }}>
        <Typography variant="h6" component="h2">Feature block #{blockNumber}</Typography>

        <Box>
          <StepTitle>1. Mark it in DevTools</StepTitle>
          <Stack direction="row" spacing={0.75} sx={{ alignItems: "center", bgcolor: tokens.subtle, borderRadius: "6px", px: 1, py: 0.5 }}>
            <Typography component="code" sx={{ flex: 1, fontFamily: "ui-monospace, Menlo, monospace", fontSize: 11, color: "text.primary" }}>
              {MARK_COMMAND}
            </Typography>
            <IconButton size="small" aria-label="Copy command" onClick={() => navigator.clipboard.writeText(MARK_COMMAND)} sx={{ p: 0.25 }}>
              <ContentCopyIcon sx={{ fontSize: 16 }} />
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
                  onClick={() => onSelectType(type.id)}
                  sx={{
                    minHeight: 0,
                    py: 0.75,
                    px: 0.5,
                    fontSize: 12,
                    lineHeight: 1.3,
                    ...(selected && {
                      bgcolor: tokens.accentBg,
                      color: tokens.accentText,
                      borderColor: tokens.accentBorder,
                      "&:hover": { bgcolor: tokens.accentBg, borderColor: tokens.accentBorder },
                    }),
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

        <Box sx={{ borderTop: `0.5px solid ${tokens.border}`, pt: 1.25 }}>
          <StepTitle>{`Accepted on this SERP (${accepted.length})`}</StepTitle>
          {accepted.map((block) => (
            <Stack key={block.index} direction="row" sx={{ alignItems: "center", py: 0.25 }}>
              <Typography variant="caption" color="text.secondary" sx={{ flex: 1 }}>
                #{block.index} {block.label}
              </Typography>
              <IconButton size="small" aria-label="Remove" onClick={() => onRemove(block.index)} disabled={busy} sx={{ p: 0.25 }}>
                <CloseIcon sx={{ fontSize: 14 }} />
              </IconButton>
            </Stack>
          ))}
        </Box>
      </Stack>

      <Stack spacing={0.75} sx={{ p: 1.5, pt: 1 }}>
        {message && <InlineError>{message}</InlineError>}
        <Button variant="contained" fullWidth onClick={onSave} disabled={busy}>
          Save and next<Kbd onAccent>3</Kbd>
        </Button>
        <Stack direction="row" spacing={0.75}>
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
