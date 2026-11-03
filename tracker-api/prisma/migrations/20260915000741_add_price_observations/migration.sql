-- CreateTable
CREATE TABLE "PriceObservation" (
    "id" UUID NOT NULL,
    "listingId" UUID NOT NULL,
    "price" TEXT NOT NULL,
    "priceAmount" INTEGER,
    "observedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "PriceObservation_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "PriceObservation_listingId_observedAt_idx" ON "PriceObservation"("listingId", "observedAt");

-- AddForeignKey
ALTER TABLE "PriceObservation" ADD CONSTRAINT "PriceObservation_listingId_fkey" FOREIGN KEY ("listingId") REFERENCES "Listing"("id") ON DELETE CASCADE ON UPDATE CASCADE;
