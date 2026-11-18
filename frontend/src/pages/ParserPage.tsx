import { useCallback, useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import CenteredCard from "../components/CenteredCard";
import InlineError from "../components/InlineError";
import TopBar from "../components/workspace/TopBar";
import SerpFrame from "../components/workspace/SerpFrame";
import ParserPanel, { type TryResult, type TypeOnSerp } from "../components/parser/ParserPanel";
import { getAnnotation, listAnnotations, listAnnotationsOfType } from "../api/annotations";
import { getFeatureTypes } from "../api/featureTypes";
import { createParser, deleteParser, linkParser, listParsers, tryXpath } from "../api/parsers";
import { getSerpHtml } from "../api/serps";
import { injectOutlineStyles, showParsed, showSavedBlocks } from "../workspace/blocks";
import type { AnnotationOutput, AnnotationSummary } from "../types/editor";
import type { ParserOutput } from "../types/parser";

// the backend's own message (e.g. lxml's xpath error) is more useful than a generic one
function errorText(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error) && typeof error.response?.data?.detail === "string") return error.response.data.detail;
  return fallback;
}

// /parsers/:providerId/:year — design parsers on one group's annotated SERPs, one SERP at a time
// /parsers/:providerId/type/:featureType — one feature type only, on its SERPs of every year
function ParserPage() {
  const { providerId = "", year = "", featureType } = useParams();
  const navigate = useNavigate();
  const providerName = (useLocation().state as { provider?: string } | null)?.provider ?? providerId.slice(0, 8);
  const [serps, setSerps] = useState<AnnotationSummary[] | null>(null);
  const [labels, setLabels] = useState<Record<string, string>>({});
  const [loadError, setLoadError] = useState<string | null>(null);
  const [position, setPosition] = useState(0);

  useEffect(() => {
    const loading = featureType ? listAnnotationsOfType(providerId, featureType) : listAnnotations(providerId, Number(year));
    loading.then(setSerps).catch(() => setLoadError("Couldn't load this group. Is the backend running?"));
    getFeatureTypes()
      .then((types) => setLabels(Object.fromEntries(types.map((t) => [t.id, t.label]))))
      .catch(() => setLoadError("Couldn't load the categories."));
  }, [providerId, year, featureType]);

  if (loadError) return <CenteredCard><InlineError>{loadError}</InlineError></CenteredCard>;
  if (serps === null) return <CenteredCard><Typography color="text.secondary">Loading…</Typography></CenteredCard>;
  if (serps.length === 0) {
    return (
      <CenteredCard>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
          {featureType ? "No SERPs have this feature type." : "This group has no annotations."}
        </Typography>
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
        year={featureType ? serps[position].year : Number(year)}
        onPrev={() => setPosition((p) => p - 1)}
        onNext={() => setPosition((p) => p + 1)}
        onExit={() => navigate("/")}
        exitLabel="Back to start"
      />
      {/* keyed by SERP: every SERP starts fresh, with its own page, annotation and result */}
      <ParserSession key={serpId} serpId={serpId} providerId={providerId} labels={labels} onlyType={featureType} />
    </Box>
  );
}

// the blocks of each feature type on this SERP, in page order
function typesOnSerp(annotation: AnnotationOutput): TypeOnSerp[] {
  const byType = new Map<string, TypeOnSerp>();
  for (const f of annotation.features) {
    const entry = byType.get(f.feature_type) ?? { featureType: f.feature_type, blocks: [] };
    entry.blocks.push({ node: f.node, parserId: f.parser_id });
    byType.set(f.feature_type, entry);
  }
  return [...byType.values()];
}

type ParserSessionProps = {
  serpId: string;
  providerId: string;
  labels: Record<string, string>;
  onlyType?: string; // set: only this type's section (the other blocks still show green in the page)
};

function ParserSession({ serpId, providerId, labels, onlyType }: ParserSessionProps) {
  const [html, setHtml] = useState<string | null>(null);
  const [serpError, setSerpError] = useState<string | null>(null);
  const [annotation, setAnnotation] = useState<AnnotationOutput | null>(null);
  const [parsers, setParsers] = useState<ParserOutput[]>([]);
  const [doc, setDoc] = useState<Document | null>(null);
  const [result, setResult] = useState<TryResult | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // the annotation (blocks and their links) and the provider's parsers change when
  // parsers are saved, used or deleted, so they're reloaded together
  const reload = useCallback(
    () => Promise.all([getAnnotation(serpId).then(setAnnotation), listParsers(providerId).then(setParsers)]),
    [serpId, providerId],
  );

  useEffect(() => {
    let cancelled = false;
    getSerpHtml(serpId)
      .then((page) => { if (!cancelled) setHtml(page); })
      .catch(() => { if (!cancelled) setSerpError("This SERP couldn't be loaded."); });
    reload().catch(() => { if (!cancelled) setMessage("Couldn't load this SERP's annotation or the parsers."); });
    return () => { cancelled = true; };
  }, [serpId, reload]);

  function handleReady(frameDoc: Document) {
    injectOutlineStyles(frameDoc);
    showSavedBlocks(frameDoc);
    setDoc(frameDoc);
  }

  // blue rings on what the last xpath tried here found
  useEffect(() => {
    if (doc) showParsed(doc, result?.output.found ?? []);
  }, [doc, result]);

  async function run(action: () => Promise<void>, failure: string) {
    setBusy(true);
    setMessage(null);
    setNotice(null);
    try {
      await action();
    } catch (error) {
      setMessage(errorText(error, failure));
    } finally {
      setBusy(false);
    }
  }

  function handleTry(featureType: string, xpath: string) {
    run(async () => setResult({ featureType, xpath, output: await tryXpath(serpId, featureType, xpath) }), "Parsing failed.");
  }

  async function handleSaveNew(featureType: string, xpath: string): Promise<boolean> {
    let saved = false;
    await run(async () => {
      await createParser(serpId, featureType, xpath);
      await reload();
      setNotice("Saved as a new parser and linked to this SERP's blocks it finds.");
      saved = true;
    }, "Saving the parser failed.");
    return saved;
  }

  function handleUse(parserId: string) {
    run(async () => {
      const { linked } = await linkParser(parserId, serpId);
      await reload();
      setNotice(`Parser linked to ${linked.length} block(s) on this SERP.`);
    }, "Using the parser failed.");
  }

  function handleDelete(parserId: string) {
    run(async () => {
      await deleteParser(parserId);
      await reload();
      setNotice("Parser deleted, and unlinked from every SERP.");
    }, "Deleting the parser failed.");
  }

  return (
    <Box sx={{ flex: 1, minHeight: 0, display: "flex", gap: 1.25 }}>
      <SerpFrame html={html} error={serpError} onReady={handleReady} />
      <ParserPanel
        types={annotation ? typesOnSerp(annotation).filter((t) => !onlyType || t.featureType === onlyType) : []}
        labels={labels}
        parsers={parsers}
        result={result}
        onTry={handleTry}
        onSaveNew={handleSaveNew}
        onUse={handleUse}
        onDelete={handleDelete}
        message={message}
        notice={notice}
        busy={busy}
      />
    </Box>
  );
}

export default ParserPage;
