import { Readability } from "@mozilla/readability";
const excluded =
  'script,style,nav,footer,aside,button,noscript,form,[hidden],[aria-hidden="true"],[role="navigation"],[role="banner"],.advertisement,.ads,.comments,#comments';
export function visible(element: Element): boolean {
  if (element.closest(excluded)) return false;
  for (let node: Element | null = element; node; node = node.parentElement) {
    const style = node.ownerDocument.defaultView?.getComputedStyle(node);
    if (style?.display === "none" || style?.visibility === "hidden")
      return false;
  }
  return true;
}
export function extractArticle(document: Document): {
  text: string;
  title: string;
} {
  const clone = document.cloneNode(true) as Document;
  const live = Array.from(document.querySelectorAll("*"));
  const copied = Array.from(clone.querySelectorAll("*"));
  // Both snapshots have the same order before removals; visibility comes from the live DOM.
  copied.forEach((element, index) => {
    if (live[index] && !visible(live[index])) element.remove();
  });
  clone.querySelectorAll(excluded).forEach((node) => node.remove());
  const result = new Readability(clone).parse();
  if (!result?.content)
    throw new Error(
      "No se encuentra un artículo legible en esta página. Selecciona el texto.",
    );
  const parser = new DOMParser();
  const article = parser.parseFromString(result.content, "text/html");
  article.querySelectorAll(excluded).forEach((element) => element.remove());
  const paragraphs = Array.from(
    article.querySelectorAll("h1,h2,h3,h4,p,li,blockquote"),
  )
    .filter((element) => !element.parentElement?.closest("li,blockquote"))
    .map((element) => element.textContent?.trim())
    .filter(Boolean);
  const text =
    paragraphs.join("\n\n") || article.body.textContent?.trim() || "";
  return {
    text: text.slice(0, 200_000),
    title: result.title || document.title,
  };
}
export function extractFrom(
  document: Document,
  target: Element | null,
): { text: string; title: string } {
  if (!target)
    throw new Error(
      "Activa primero «Leer desde aquí» y elige un párrafo de la página.",
    );
  const root = target.closest('article,main,[role="main"]') ?? document.body;
  const paragraphs = Array.from(
    root.querySelectorAll("h1,h2,h3,h4,p,li,blockquote"),
  ).filter(
    (element) =>
      visible(element) && !element.parentElement?.closest("li,blockquote"),
  );
  const start = paragraphs.findIndex(
    (element) =>
      element === target ||
      element.contains(target) ||
      target.contains(element),
  );
  if (start < 0) throw new Error("Elige un párrafo del contenido principal.");
  return {
    text: paragraphs
      .slice(start)
      .map((element) => element.textContent?.trim())
      .filter(Boolean)
      .join("\n\n")
      .slice(0, 200_000),
    title: document.title,
  };
}
