import { gql, useQuery } from '@apollo/client';


const GET_ZOHO_SKU_TRACK_INFO = gql`
  {
    allZohoSkuTrackInfo {
      id
      skuTracked
      skuMatched
      skuMissing
      skuExcess
      date
    }
  }
`;

export const useSkuTrackInfoQuery = () => {
  const { loading, error, data, refetch } = useQuery(GET_ZOHO_SKU_TRACK_INFO);

  return { loading, error, data: data?.allZohoSkuTrackInfo || [], refetch };
};