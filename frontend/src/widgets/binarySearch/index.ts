import type { WidgetDefinition } from '../registry';
import { BinarySearch, type BinarySearchState } from './BinarySearch';

/** `widget_state` = las posiciones abiertas, en orden. */
const binarySearch: WidgetDefinition<BinarySearchState> = {
  render: BinarySearch,
  serialize: (state) => state.probes,
};

export default binarySearch;
