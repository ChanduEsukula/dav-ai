type ProductScanTeaserProps = {
  openProductScan: () => void
}

function ProductScanTeaser({ openProductScan }: ProductScanTeaserProps) {
  return (
    <section className="productscan-teaser" aria-label="Experimental ProductScan">
      <div>
        <p className="eyebrow">Experimental ProductScan</p>
        <h2>Turn visible label text into a search starting point.</h2>
        <p>
          Upload a local label image for preview, paste readable text, review deterministic
          candidate terms, then choose the existing Dav AI workflow to search.
        </p>
      </div>

      <button type="button" onClick={openProductScan}>
        Open ProductScan
      </button>
    </section>
  )
}

export default ProductScanTeaser
