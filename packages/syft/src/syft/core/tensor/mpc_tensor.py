# stdlib
from functools import lru_cache

# third party
import numpy as np

# syft absolute
from syft.core.tensor.passthrough import PassthroughTensor
from syft.core.tensor.share_tensor import ShareTensor


def is_pointer(val):
    if "Pointer" in type(val).__name__:
        return True


class MPCTensor(PassthroughTensor):
    def __init__(self, parties=None, secret=None, shares=None, shape=None):
        if secret is None and shares is None:
            raise ValueError("Secret or shares should be populated!")

        if secret is not None:
            shares = MPCTensor._get_shares_from_secret(
                secret=secret, nr_parties=len(parties), shape=shape
            )

        res = MPCTensor._mpc_from_shares(shares, parties)

        super().__init__(res)

    @staticmethod
    def _mpc_from_shares(shares, parties):
        if not isinstance(shares, list):
            raise ValueError("_mpc_from_shares expected a list of shares")

        if is_pointer(shares[0]):
            # Remote shares
            return shares
        else:
            MPCTensor._mpc_from_local_shares(shares, parties)

    @staticmethod
    def _mpc_from_local_shares(shares, parties):
        # TODO: ShareTensor needs to have serde serializer/deserializer
        shares_ptr = [share.send(party) for share, party in zip(shares, parties)]
        return shares_ptr

    @staticmethod
    def _get_shares_from_secret(secret, nr_parties, shape=None):
        if is_pointer(secret):
            if shape is None:
                raise ValueError("Shape must be specified when the secret is remote")
            return self._from_remote_secret(secret, shape)

        return MPCTensor._get_shares_from_local_secret(secret, nr_parties)

    @staticmethod
    def _get_shares_from_local_secret(secret, nr_parties):
        # TODO: ShareTensor needs to have serde serializer/deserializer
        shares = ShareTensor.generate_shares(secret=secret, nr_shares=nr_parties)
        return shares

    def reconstruct(self):
        local_shares = [share.get() for share in self.child]

        result_fp = sum(local_shares)
        result = result_fp.decode()
        return result