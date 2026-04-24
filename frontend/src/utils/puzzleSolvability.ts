export function isSolvable(tiles: number[], gridSize: number): boolean {
  let inversions = 0;
  const flat = tiles.filter((t) => t !== 0);
  for (let i = 0; i < flat.length; i++) {
    for (let j = i + 1; j < flat.length; j++) {
      if (flat[i] > flat[j]) {
        inversions++;
      }
    }
  }

  if (gridSize % 2 === 1) {
    return inversions % 2 === 0;
  }

  const emptyIdx = tiles.indexOf(0);
  if (emptyIdx === -1) return false;

  const emptyRow = Math.floor(emptyIdx / gridSize);
  const rowFromBottom = gridSize - emptyRow;
  
  return (rowFromBottom % 2 === 0) !== (inversions % 2 === 0);
}
