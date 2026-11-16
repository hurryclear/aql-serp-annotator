import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import IconButton from "@mui/material/IconButton";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import CloseIcon from "@mui/icons-material/Close";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import InlineError from "../InlineError";
import { tokens } from "../../theme";
import type { FeatureType } from "../../types/workspace";
import type { EditorBlock } from "../../types/editor";

const MARK_COMMAND = "$0.classList.add('aqlqa-sf-testing')";

type EditPanelProps = {
  blocks: EditorBlock[];
  unplaced: number; // features saved before element marking: no position, can't be shown
  featureTypes: FeatureType[];
  onChangeType: (index: number, featureType: string) => void;
  onRemove: (index: number) => void;
  addType: string;
  onAddTypeChange: (featureType: string) => void;
  onAdd: () => void;
  onSave: () => void;
  onToggleGroundTruth: () => void;
  groundTruth: boolean;
  dirty: boolean;
  createdBy: string;
  message: string | null;
  notice: string | null;
  busy: boolean;
};

function SectionTitle({ children }: { children: string }) {
  return <Typography variant="subtitle2" sx={{ mb: 0.75 }}>{children}</Typography>;
}

function TypeSelect({ value, featureTypes, onChange, disabled, placeholder }: {
  value: string; featureTypes: FeatureType[]; onChange: (v: string) => void; disabled?: boolean; placeholder?: string;
}) {
  return (
    <Select
      size="small"
      fullWidth
      displayEmpty
      value={value}
      disabled={disabled}
      onChange={(e) => onChange(e.target.value)}
      sx={{ fontSize: 13 }}
      renderValue={(v) => featureTypes.find((t) => t.id === v)?.label ?? <span style={{ color: tokens.textMuted }}>{placeholder ?? v}</span>}
    >
      {featureTypes.map((t) => <MenuItem key={t.id} value={t.id} sx={{ fontSize: 13 }}>{t.label}</MenuItem>)}
    </Select>
  );
}

function EditPanel(props: EditPanelProps) {
  const {
    blocks, unplaced, featureTypes, onChangeType, onRemove, addType, onAddTypeChange, onAdd,
    onSave, onToggleGroundTruth, groundTruth, dirty, createdBy, message, notice, busy,
  } = props;

  return (
    <Card sx={{ width: 300, flexShrink: 0, display: "flex", flexDirection: "column", borderRadius: 1 }}>
      <Stack spacing={1.75} sx={{ p: 1.5, overflowY: "auto", flex: 1 }}>
        <Box>
          <Typography variant="h6" component="h2">Features on this SERP ({blocks.length})</Typography>
          <Typography variant="caption" color="text.secondary">
            Annotated by {createdBy} · {groundTruth ? "ground truth ✓" : "not confirmed yet"}
          </Typography>
        </Box>

        <Stack spacing={0.75}>
          {blocks.length === 0 && (
            <Typography variant="body2" color="text.secondary">No features. Add one below, or keep it as "No features".</Typography>
          )}
          {blocks.map((block, i) => (
            <Stack key={block.index} direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
              <Typography variant="caption" color="text.secondary" sx={{ width: 22 }}>#{i + 1}</Typography>
              <TypeSelect value={block.type} featureTypes={featureTypes} onChange={(t) => onChangeType(block.index, t)} disabled={busy} />
              <IconButton size="small" aria-label="Delete feature" onClick={() => onRemove(block.index)} disabled={busy} sx={{ p: 0.25 }}>
                <CloseIcon sx={{ fontSize: 16 }} />
              </IconButton>
            </Stack>
          ))}
          {unplaced > 0 && (
            <InlineError>
              {`${unplaced} saved feature(s) have no position on the page (saved before element marking). Saving changes drops them; mark them again to keep them.`}
            </InlineError>
          )}
        </Stack>

        <Box sx={{ borderTop: `0.5px solid ${tokens.border}`, pt: 1.25 }}>
          <SectionTitle>Add a feature</SectionTitle>
          <Typography variant="caption" color="text.secondary" component="p" sx={{ mb: 0.5 }}>1. Mark it in DevTools</Typography>
          <Stack direction="row" spacing={0.75} sx={{ alignItems: "center", bgcolor: tokens.subtle, borderRadius: "6px", px: 1, py: 0.5, mb: 1 }}>
            <Typography component="code" sx={{ flex: 1, fontFamily: "ui-monospace, Menlo, monospace", fontSize: 11 }}>
              {MARK_COMMAND}
            </Typography>
            <IconButton size="small" aria-label="Copy command" onClick={() => navigator.clipboard.writeText(MARK_COMMAND)} sx={{ p: 0.25 }}>
              <ContentCopyIcon sx={{ fontSize: 16 }} />
            </IconButton>
          </Stack>
          <Typography variant="caption" color="text.secondary" component="p" sx={{ mb: 0.5 }}>2. Choose a category, then add</Typography>
          <Stack direction="row" spacing={0.75}>
            <TypeSelect value={addType} featureTypes={featureTypes} onChange={onAddTypeChange} disabled={busy} placeholder="Category…" />
            <Button variant="outlined" onClick={onAdd} disabled={busy}>Add</Button>
          </Stack>
        </Box>
      </Stack>

      <Stack spacing={0.75} sx={{ p: 1.5, pt: 1 }}>
        {message && <InlineError>{message}</InlineError>}
        {notice && !message && <Typography variant="body2" sx={{ color: "success.main" }}>{notice}</Typography>}
        <Button variant="contained" fullWidth onClick={onSave} disabled={busy || !dirty}>
          {dirty ? "Save changes" : "No unsaved changes"}
        </Button>
        {/* one button for both directions: confirm, or take a confirmation back */}
        <Button variant="outlined" fullWidth onClick={onToggleGroundTruth} disabled={busy}>
          {groundTruth ? "Unconfirm ground truth" : "Confirm as ground truth"}
        </Button>
      </Stack>
    </Card>
  );
}

export default EditPanel;
