import { Helmet } from "react-helmet-async";

const DEFAULT_OG_IMAGE = process.env.REACT_APP_OG_IMAGE_URL || "";
const SITE = process.env.REACT_APP_SITE_NAME || "Stonebridge Construction Co.";

export default function SEO({ title, description, image, path = "" }) {
  const fullTitle = title ? `${title} — ${SITE}` : `${SITE} — Building, Renovation & Project Management`;
  const desc = description || "A Denver-based construction studio building residential, commercial, and renovation projects since 1998. View our portfolio or start a new project.";
  const img = image || DEFAULT_OG_IMAGE;
  const url = typeof window !== "undefined"
    ? `${window.location.origin}${path || window.location.pathname}`
    : path;

  return (
    <Helmet>
      <title>{fullTitle}</title>
      <meta name="description" content={desc} />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={desc} />
      <meta property="og:image" content={img} />
      <meta property="og:url" content={url} />
      <meta property="og:type" content="website" />
      <meta property="og:site_name" content={SITE} />
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={desc} />
      <meta name="twitter:image" content={img} />
      <link rel="canonical" href={url} />
    </Helmet>
  );
}
