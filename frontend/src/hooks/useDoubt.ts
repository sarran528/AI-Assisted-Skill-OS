import { useMutation } from "@tanstack/react-query";

import { askDoubt } from "../api/support";

export function useDoubt() {
  return useMutation({
    mutationFn: askDoubt,
  });
}
