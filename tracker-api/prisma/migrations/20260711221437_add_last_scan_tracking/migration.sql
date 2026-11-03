-- AlterTable
ALTER TABLE "Listing" ADD COLUMN     "savedSearchId" UUID;

-- AlterTable
ALTER TABLE "SavedSearch" ADD COLUMN     "lastRunNewListingIds" TEXT[] DEFAULT ARRAY[]::TEXT[],
ADD COLUMN     "lastSkippedDuplicates" INTEGER NOT NULL DEFAULT 0,
ADD COLUMN     "lastTotalScraped" INTEGER NOT NULL DEFAULT 0;
