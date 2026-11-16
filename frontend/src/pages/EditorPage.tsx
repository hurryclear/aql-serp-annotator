import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import Typography from "@mui/material/Typography";
import CenteredCard from "../components/CenteredCard";
import InlineError from "../components/InlineError";
import TopBar from "../components/workspace/TopBar";
import SerpFrame from "../components/workspace/SerpFrame";
import EditPanel from "../components/editor/EditPanel";
import { getFeatureTypes } from "../api/featureTypes";
import { getSerpHtml } from "../api/serps";
import { getAnnotation, listAnnotations, replaceAnnotation, setGroundTruth } from "../api/annotations";
import { elementByNode, findMarkedElement, injectOutlineStyles, markAccepted, setBlockType, unmarkAccepted } from "../workspace/blocks";
import type { FeatureType } from "../types/workspace";
import type { AnnotationOutput, AnnotationSummary, EditorBlock } from "../types/editor";

// /editor/:providerId/:year — go through one group's annotated SERPs, one at a time
function EditorPage() {
  const { providerId = "", year = "" } = useParams();
  const navigate = useNavigate();
  // the home page passes the provider's name along; after a reload, show the id's start
  const providerName = (useLocation().state as { provider?: string } | null)?.provider ?? providerId.slice(0, 8);
  const [serps, setSerps] = useState<AnnotationSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [position, setPosition] = useState(0);
  const [featureTypes, setFeatureTypes] = useState<FeatureType[]>([]);
  const [dirty, setDirty] = useState(false);
  // where to go once the annotator agrees to drop unsaved changes
  const [pendingMove, setPendingMove] = useState<(() => void) | null>(null);

  useEffect(() => {
    listAnnotations(providerId, Number(year))
      .then(setSerps)
      .catch(() => setError("Couldn't load this group. Check that the backend is running, then reload."));
    getFeatureTypes().then(setFeatureTypes).catch(() => setError("Couldn't load the categories. Reload the page to try again."));
  }, [providerId, year]);

  // unsaved edits are lost when the SERP changes, so ask first
  function move(action: () => void) {
    if (dirty) setPendingMove(() => action);
    else action();
  }

  if (error) return <CenteredCard><InlineError>{error}</InlineError></CenteredCard>;
  if (serps === null) return <CenteredCard><Typography color="text.secondary">Loading…</Typography></CenteredCard>;
  if (serps.length === 0) {
    return (
      <CenteredCard>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>This group has no annotations.</Typography>
        <Button variant="outlined" fullWidth onClick={() => navigate("/")}>Back to start</Button>
      </CenteredCard>
    );
  }

  const serpId = serps[position].serp_id;
  return (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column", gap: 1.25, p: 1.25 }}>
      <TopBar
        position={position + 1}
        total={serps.length}
        serpId={serpId}
        provider={providerName}
        year={Number(year)}
        onPrev={() => move(() => setPosition((p) => p - 1))}
        onNext={() => move(() => setPosition((p) => p + 1))}
        onExit={() => move(() => navigate("/"))}
        exitLabel="Back to start"
      />
      {/* keyed by SERP: every SERP starts from its saved state */}
      <EditorSession key={serpId} serpId={serpId} featureTypes={featureTypes} onDirtyChange={setDirty} />
      <Dialog open={pendingMove !== null} onClose={() => setPendingMove(null)}>
        <DialogContent>
          <DialogContentText>This SERP has unsaved changes. Leave it and lose them?</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button variant="outlined" onClick={() => setPendingMove(null)}>Stay</Button>
          <Button
            variant="outlined"
            sx={{ color: "error.main" }}
            onClick={() => { const action = pendingMove; setPendingMove(null); setDirty(false); action?.(); }}
          >
            Leave without saving
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

type EditorSessionProps = {
  serpId: string;
  featureTypes: FeatureType[];
  onDirtyChange: (dirty: boolean) => void;
};

function EditorSession({ serpId, featureTypes, onDirtyChange }: EditorSessionProps) {
  const [html, setHtml] = useState<string | null>(null);
  const [serpError, setSerpError] = useState<string | null>(null);
  const [annotation, setAnnotation] = useState<AnnotationOutput | null>(null);
  const [doc, setDoc] = useState<Document | null>(null);
  const [blocks, setBlocks] = useState<EditorBlock[]>([]);
  const [unplaced, setUnplaced] = useState(0);
  const [addType, setAddType] = useState("");
  const [dirty, setDirty] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const placedRef = useRef(false);

  const nextIndex = blocks.reduce((max, b) => Math.max(max, b.index), 0) + 1;

  useEffect(() => {
    let cancelled = false;
    getSerpHtml(serpId)
      .then((page) => { if (!cancelled) setHtml(page); })
      .catch(() => { if (!cancelled) setSerpError("This SERP couldn't be loaded."); });
    getAnnotation(serpId)
      .then((a) => { if (!cancelled) setAnnotation(a); })
      .catch(() => { if (!cancelled) setMessage("Couldn't load this annotation."); });
    return () => { cancelled = true; };
  }, [serpId]);

  function changeDirty(value: boolean) {
    setDirty(value);
    onDirtyChange(value);
  }

  function handleReady(frameDoc: Document) {
    injectOutlineStyles(frameDoc);
    setDoc(frameDoc);
  }

  // once both the page and the annotation are here: highlight the saved features
  useEffect(() => {
    if (!doc || !annotation || placedRef.current) return;
    placedRef.current = true;
    const placed: EditorBlock[] = [];
    annotation.features.forEach((feature) => {
      const element = feature.node === null ? null : elementByNode(doc, feature.node);
      if (!element || feature.node === null) return;
      const index = placed.length + 1;
      markAccepted(element, index, feature.feature_type);
      placed.push({ index, type: feature.feature_type, node: feature.node });
    });
    setBlocks(placed);
    setUnplaced(annotation.features.length - placed.length);
  }, [doc, annotation]);

  function handleChangeType(index: number, featureType: string) {
    if (doc) setBlockType(doc, index, featureType);
    setBlocks(blocks.map((b) => (b.index === index ? { ...b, type: featureType } : b)));
    setNotice(null);
    changeDirty(true);
  }

  function handleRemove(index: number) {
    if (doc) unmarkAccepted(doc, index);
    setBlocks(blocks.filter((b) => b.index !== index));
    setNotice(null);
    changeDirty(true);
  }

  function handleAdd() {
    if (!doc) return setMessage(serpError ?? "The SERP is still loading.");
    const result = findMarkedElement(doc);
    if ("error" in result) return setMessage(result.error);
    if (!addType) return setMessage("Choose a category first.");
    markAccepted(result.element, nextIndex, addType);
    setBlocks([...blocks, { index: nextIndex, type: addType, node: result.node }]);
    setAddType("");
    setMessage(null);
    setNotice(null);
    changeDirty(true);
  }

  async function handleSave() {
    setBusy(true);
    setMessage(null);
    try {
      const saved = await replaceAnnotation(serpId, blocks.map((b) => ({ feature_type: b.type, node: b.node })));
      setAnnotation(saved);
      setUnplaced(0);
      changeDirty(false);
      setNotice("Saved. The annotation needs confirming again.");
    } catch {
      setMessage("Saving failed. Your changes are kept. Try again.");
    } finally {
      setBusy(false);
    }
  }

  // confirm, or take a confirmation back. Confirming needs the saved state, since
  // that's what gets confirmed; unconfirming touches no features, so it always works
  async function handleToggleGroundTruth() {
    const confirm = !(annotation?.ground_truth ?? false);
    if (confirm && dirty) return setMessage("Save your changes before confirming.");
    setBusy(true);
    setMessage(null);
    try {
      setAnnotation(await setGroundTruth(serpId, confirm));
      setNotice(confirm ? "Confirmed as ground truth." : "No longer ground truth.");
    } catch {
      setMessage(confirm ? "Confirming failed. Try again." : "Unconfirming failed. Try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Box sx={{ flex: 1, minHeight: 0, display: "flex", gap: 1.25 }}>
      <SerpFrame html={html} error={serpError} onReady={handleReady} />
      <EditPanel
        blocks={blocks}
        unplaced={unplaced}
        featureTypes={featureTypes}
        onChangeType={handleChangeType}
        onRemove={handleRemove}
        addType={addType}
        onAddTypeChange={setAddType}
        onAdd={handleAdd}
        onSave={handleSave}
        onToggleGroundTruth={handleToggleGroundTruth}
        groundTruth={annotation?.ground_truth ?? false}
        dirty={dirty}
        createdBy={annotation?.created_by ?? "…"}
        message={message}
        notice={notice}
        busy={busy}
      />
    </Box>
  );
}

export default EditorPage;
