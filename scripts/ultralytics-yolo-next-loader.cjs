"use strict";

const INDIRECT_IMPORT = "import(/* @vite-ignore */ pkg)";
const BUNDLED_IMPORT = 'import("@litertjs/core")';

module.exports = function ultralyticsYoloNextLoader(source) {
  const occurrences = source.split(INDIRECT_IMPORT).length - 1;
  if (occurrences !== 1) {
    throw new Error(
      "Expected one Ultralytics LiteRT optional-peer import. "
      + "Review @ultralytics/yolo before updating the pinned package.",
    );
  }
  return source.replace(INDIRECT_IMPORT, BUNDLED_IMPORT);
};
