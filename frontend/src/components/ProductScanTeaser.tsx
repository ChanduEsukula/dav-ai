type ProductScanTeaserProps = {
  openProductScan: () => void
}

function ProductScanTeaser({ openProductScan }: ProductScanTeaserProps) {
  return (
    <section className="productscan-teaser" aria-label="Experimental ProductScan">
      <div>
        <p className="eyebrow">Experimental ProductScan</p>
        <h2>Turn label text into a safer search handoff.</h2>
        <p>
          Preview a label locally, review extracted or pasted text, choose a confirmed term, then hand it off to DrugSignal, FoodSignal, or Personal Care Signals.
        </p>
      </div>

      <button type="button" onClick={openProductScan}>
        Open Scan beta
      </button>
    </section>
  )
}

export default ProductScanTeaser
