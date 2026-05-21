-- Add simple_headline for board/simple-mode display.
--
-- Nullable so existing cards remain valid. New cards generated after this
-- migration will always populate it. The UI falls back to the first sentence
-- of board_talking_point when null (for any cards written before this change).
ALTER TABLE provocation_cards
  ADD COLUMN simple_headline TEXT;
