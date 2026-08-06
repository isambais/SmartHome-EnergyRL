import { useEffect, useState } from "react";
import { api } from "../api.js";

/** 3D bina görünümü — backend'in three.js HTML'ini iframe'e gömer */
export default function Building({ cfg, saat, soc, gunesKw, kesinti = false, height = 500 }) {
  const [html, setHtml] = useState("");

  useEffect(() => {
    let ok = true;
    api.buildingHtml({ config: cfg, saat, soc, gunes_kw: gunesKw, kesinti, height })
      .then((h) => ok && setHtml(h))
      .catch(() => {});
    return () => { ok = false; };
  }, [JSON.stringify(cfg), saat, soc?.toFixed(2), gunesKw?.toFixed(1), kesinti, height]);

  return (
    <iframe
      title="bina3d"
      srcDoc={html}
      style={{ width: "100%", height: height + 12, border: "none", borderRadius: 10 }}
    />
  );
}
