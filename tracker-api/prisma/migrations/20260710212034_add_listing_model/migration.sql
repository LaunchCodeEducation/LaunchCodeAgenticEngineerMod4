-- CreateTable
CREATE TABLE "Listing" (
    "id" UUID NOT NULL,
    "source" TEXT NOT NULL,
    "listingUrl" TEXT NOT NULL,
    "title" TEXT,
    "price" TEXT,
    "location" TEXT,
    "imageUrl" TEXT,
    "seenAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "Listing_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "Listing_listingUrl_key" ON "Listing"("listingUrl");
