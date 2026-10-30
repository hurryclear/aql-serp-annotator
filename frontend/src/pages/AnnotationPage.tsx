import { useEffect, useRef, useState, type RefObject } from "react";
import { Link as RouterLink, useLocation, useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import Link from "@mui/material/Link";
import Typography from "@mui/material/Typography";
import CenteredCard from "../components/CenteredCard";
import TopBar from "../components/workspace/TopBar";
import SerpFrame from "../components/workspace/SerpFrame";
import StepPanel from "../components/workspace/StepPanel";
import DoneCard from "../components/workspace/DoneCard";
import { getFeatureTypes } from "../api/features";
import { getSerpHtml, saveAnnotation } from "../api/serps";
import { blockContent, findMarkedElement, injectOutlineStyles, markAccepted, unmarkAccepted } from "../workspace/blocks";
import { shortcutFor, type ShortcutAction } from "../workspace/shortcuts";
import type { AcceptedBlock, AnnotatedFeatureInput, FeatureType, WorkspaceState } from "../types/workspace";

// the SERP ids only arrive as router state from the landing page; a reload or a
// pasted URL loses them (ADR 0005), so there's nothing to annotate
function AnnotationPage() {
  const { cartId } = useParams();
  const state = useLocation().state as WorkspaceState | null;

  if (!cartId || !state) {
    return (
      <CenteredCard>
        <Typography variant="body1" color="text.secondary">
          This cart isn't open in this tab anymore. Start a new one from the{" "}
          <Link component={RouterLink} to="/">landing page</Link>.
        </Typography>
      </CenteredCard>
    );
  }
  // keyed by cart: moving between two workspace URLs (e.g. browser Back) starts over at SERP 1
  return <Workspace key={cartId} cartId={cartId} {...state} />;
}

function Workspace({ cartId, serpIds, provider, language, year }: WorkspaceState & { cartId: string }) {
  const navigate = useNavigate();
  const [position, setPosition] = useState(0);
  const [featureTypes, setFeatureTypes] = useState<FeatureType[]>([]);
  const [typesError, setTypesError] = useState<string | null>(null);

  useEffect(() => {
    getFeatureTypes()
      .then(setFeatureTypes)
      .catch(() => setTypesError("Couldn't load the categories. Reload the page to try again."));
  }, []);

  if (position >= serpIds.length) return <DoneCard total={serpIds.length} onBack={() => navigate("/")} />;

  const serpId = serpIds[position];
  return (
    <Box sx={{ height: "100%", display: "flex", flexDirection: "column", gap: 1.25, p: 1.25 }}>
      <TopBar position={position + 1} total={serpIds.length} provider={provider} language={language} year={year} onExit={() => navigate("/")} />
      {/* keyed by SERP: React starts a fresh session (empty blocks, no message) for every SERP */}
      <SerpSession
        key={serpId}
        cartId={cartId}
        serpId={serpId}
        featureTypes={featureTypes}
        typesError={typesError}
        onDone={() => setPosition((p) => p + 1)}
      />
    </Box>
  );
}

// listens for the 1-4 shortcuts on the page or inside the SERP iframe (key presses
// inside an iframe never reach the outer window); returns the cleanup
function listenForShortcuts(target: Window | Document, actionRef: RefObject<(action: ShortcutAction) => void>) {
  const onKeyDown = (event: Event) => {
    const action = shortcutFor(event as KeyboardEvent);
    if (action) {
      event.preventDefault();
      actionRef.current(action);
    }
  };
  target.addEventListener("keydown", onKeyDown);
  return () => target.removeEventListener("keydown", onKeyDown);
}

type SerpSessionProps = {
  cartId: string;
  serpId: string;
  featureTypes: FeatureType[];
  typesError: string | null;
  onDone: () => void;
};

function SerpSession({ cartId, serpId, featureTypes, typesError, onDone }: SerpSessionProps) {
  const [html, setHtml] = useState<string | null>(null);
  const [serpError, setSerpError] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [accepted, setAccepted] = useState<AcceptedBlock[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const docRef = useRef<Document | null>(null);
  // a ref, not just state: two quick presses of "3" both run before React re-renders,
  // and only a ref lets the second one see that a save is already running
  const busyRef = useRef(false);
  // the keydown listeners are attached once, so they call whatever this ref holds now
  const actionRef = useRef<(action: ShortcutAction) => void>(() => {});

  const nextIndex = accepted.reduce((max, block) => Math.max(max, block.index), 0) + 1;

  useEffect(() => {
    let cancelled = false;
    getSerpHtml(serpId)
      .then((page) => { if (!cancelled) setHtml(page); })
      .catch(() => { if (!cancelled) setSerpError("This SERP couldn't be loaded. Skip it to continue."); });
    return () => { cancelled = true; };
  }, [serpId]);

  useEffect(() => listenForShortcuts(window, actionRef), []);

  function handleReady(doc: Document) {
    docRef.current = doc;
    injectOutlineStyles(doc);
    // no cleanup needed: the document is thrown away with the iframe
    listenForShortcuts(doc, actionRef);
  }

  // Accept, Save and No blocks need a SERP on screen to act on
  function loadedDoc(): Document | null {
    if (!docRef.current) setMessage(serpError ?? "The SERP is still loading.");
    return docRef.current;
  }

  function handleAccept() {
    if (busyRef.current) return;
    const doc = loadedDoc();
    if (!doc) return;
    const result = findMarkedElement(doc);
    if ("error" in result) {
      setMessage(result.error);
      return;
    }
    if (!selectedType) {
      setMessage("Choose a category first.");
      return;
    }
    markAccepted(result.element, nextIndex);
    const label = featureTypes.find((type) => type.id === selectedType)?.label ?? selectedType;
    setAccepted([...accepted, { index: nextIndex, type: selectedType, label, content: blockContent(result.element) }]);
    setSelectedType(null);
    setMessage(null);
  }

  function handleRemove(index: number) {
    if (docRef.current) unmarkAccepted(docRef.current, index);
    setAccepted(accepted.filter((block) => block.index !== index));
  }

  // save this SERP's annotation, then move on; on failure keep everything and stay
  async function submit(features: AnnotatedFeatureInput[]) {
    busyRef.current = true;
    setBusy(true);
    setMessage(null);
    try {
      await saveAnnotation(serpId, cartId, features);
      onDone();
    } catch (error) {
      // already annotated (e.g. in another tab): nothing left to do here
      if (axios.isAxiosError(error) && error.response?.status === 409) onDone();
      else setMessage("Saving failed. Your blocks are kept. Try again.");
    } finally {
      busyRef.current = false;
      setBusy(false);
    }
  }

  function handleSave() {
    if (busyRef.current || !loadedDoc()) return;
    if (accepted.length === 0) {
      setMessage("No blocks accepted. Use No blocks if this SERP has none.");
      return;
    }
    submit(accepted.map((block) => ({ type: block.type, content: block.content, xpath: null })));
  }

  function handleNoBlocks() {
    if (busyRef.current || !loadedDoc()) return;
    if (accepted.length > 0) setConfirmOpen(true);
    else submit([]);
  }

  // saves nothing, so this SERP can come back in a later cart
  function handleSkip() {
    if (busyRef.current) return;
    onDone();
  }

  // runs after every render, so the listeners always reach the current handlers
  useEffect(() => {
    actionRef.current = (action) => {
      if (confirmOpen) return;
      if (action === "accept") handleAccept();
      else if (action === "save") handleSave();
      else if (action === "noBlocks") handleNoBlocks();
      else handleSkip();
    };
  });

  return (
    <Box sx={{ flex: 1, minHeight: 0, display: "flex", gap: 1.25 }}>
      <SerpFrame html={html} error={serpError} onReady={handleReady} />
      <StepPanel
        blockNumber={nextIndex}
        featureTypes={featureTypes}
        selectedType={selectedType}
        onSelectType={setSelectedType}
        onAccept={handleAccept}
        accepted={accepted}
        onRemove={handleRemove}
        onSave={handleSave}
        onNoBlocks={handleNoBlocks}
        onSkip={handleSkip}
        message={message ?? typesError}
        busy={busy}
      />
      <Dialog open={confirmOpen} onClose={() => setConfirmOpen(false)}>
        <DialogContent>
          <DialogContentText>
            Throw away {accepted.length} accepted {accepted.length === 1 ? "block" : "blocks"} and save this SERP as having none?
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button variant="outlined" onClick={() => setConfirmOpen(false)}>Cancel</Button>
          <Button variant="outlined" sx={{ color: "error.main" }} onClick={() => { setConfirmOpen(false); submit([]); }}>
            Save as no blocks
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default AnnotationPage;
