import MDXComponents from "@theme-original/MDXComponents";
import {
  Card,
  CardGroup,
  Steps,
  Step,
  Accordion,
  AccordionGroup,
  Note,
  Tip,
  Info,
  Warning,
  Check,
} from "@site/src/components/Mintlify";

// Register the Mintlify-style components globally so the migrated .mdx pages can
// use <Card>, <Steps>, <Note>, etc. without importing them in every file.
export default {
  ...MDXComponents,
  Card,
  CardGroup,
  Steps,
  Step,
  Accordion,
  AccordionGroup,
  Note,
  Tip,
  Info,
  Warning,
  Check,
};
