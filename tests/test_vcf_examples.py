import numpy as np
import numpy.testing as nt
import xarray.testing as xt
import pytest
import sgkit as sg

from bio2zarr import vcf


class TestSmallExample:
    data_path = "tests/data/vcf/sample.vcf.gz"

    @pytest.fixture(scope="class")
    def ds(self, tmp_path_factory):
        out = tmp_path_factory.mktemp("data") / "example.vcf.zarr"
        vcf.convert_vcf([self.data_path], out)
        return sg.load_dataset(out)

    def test_filters(self, ds):
        nt.assert_array_equal(ds["filter_id"], ["PASS", "s50", "q10"])
        nt.assert_array_equal(
            ds["variant_filter"],
            [
                [False, False, False],
                [False, False, False],
                [True, False, False],
                [False, False, True],
                [True, False, False],
                [True, False, False],
                [True, False, False],
                [False, False, False],
                [True, False, False],
            ],
        )

    def test_contigs(self, ds):
        nt.assert_array_equal(ds["contig_id"], ["19", "20", "X"])
        assert "contig_length" not in ds
        nt.assert_array_equal(ds["variant_contig"], [0, 0, 1, 1, 1, 1, 1, 1, 2])

    def test_position(self, ds):
        nt.assert_array_equal(
            ds["variant_position"],
            [111, 112, 14370, 17330, 1110696, 1230237, 1234567, 1235237, 10],
        )

    def test_int_info_fields(self, ds):
        nt.assert_array_equal(
            ds["variant_NS"],
            [-1, -1, 3, 3, 2, 3, 3, -1, -1],
        )
        nt.assert_array_equal(
            ds["variant_AN"],
            [-1, -1, -1, -1, -1, -1, 6, -1, -1],
        )

        nt.assert_array_equal(
            ds["variant_AC"],
            [
                [-1, -1],
                [-1, -1],
                [-1, -1],
                [-1, -1],
                [-1, -1],
                [-1, -1],
                [3, 1],
                [-1, -1],
                [-1, -1],
            ],
        )

    def test_float_info_fields(self, ds):
        missing = vcf.FLOAT32_MISSING
        fill = vcf.FLOAT32_FILL
        variant_AF = np.array(
            [
                [missing, missing],
                [missing, missing],
                [0.5, fill],
                [0.017, fill],
                [0.333, 0.667],
                [missing, missing],
                [missing, missing],
                [missing, missing],
                [missing, missing],
            ],
            dtype=np.float32,
        )
        values = ds["variant_AF"].values
        nt.assert_array_almost_equal(values, variant_AF, 3)
        nans = np.isnan(variant_AF)
        nt.assert_array_equal(
            variant_AF.view(np.int32)[nans], values.view(np.int32)[nans]
        )

    def test_string_info_fields(self, ds):
        nt.assert_array_equal(
            ds["variant_AA"],
            [
                ".",
                ".",
                ".",
                ".",
                "T",
                "T",
                "G",
                ".",
                ".",
            ],
        )

    def test_flag_info_fields(self, ds):
        nt.assert_array_equal(
            ds["variant_DB"],
            [
                False,
                False,
                True,
                False,
                True,
                False,
                False,
                False,
                False,
            ],
        )

    def test_allele(self, ds):
        fill = vcf.STR_FILL
        nt.assert_array_equal(
            ds["variant_allele"].values.tolist(),
            [
                ["A", "C", fill, fill],
                ["A", "G", fill, fill],
                ["G", "A", fill, fill],
                ["T", "A", fill, fill],
                ["A", "G", "T", fill],
                ["T", fill, fill, fill],
                ["G", "GA", "GAC", fill],
                ["T", fill, fill, fill],
                ["AC", "A", "ATG", "C"],
            ],
        )
        assert ds["variant_allele"].dtype == "O"

    def test_id(self, ds):
        nt.assert_array_equal(
            ds["variant_id"].values.tolist(),
            [".", ".", "rs6054257", ".", "rs6040355", ".", "microsat1", ".", "rsTest"],
        )
        assert ds["variant_id"].dtype == "O"
        nt.assert_array_equal(
            ds["variant_id_mask"],
            [True, True, False, True, False, True, False, True, False],
        )

    def test_samples(self, ds):
        nt.assert_array_equal(ds["sample_id"], ["NA00001", "NA00002", "NA00003"])

    def test_call_genotype(self, ds):
        call_genotype = np.array(
            [
                [[0, 0], [0, 0], [0, 1]],
                [[0, 0], [0, 0], [0, 1]],
                [[0, 0], [1, 0], [1, 1]],
                [[0, 0], [0, 1], [0, 0]],
                [[1, 2], [2, 1], [2, 2]],
                [[0, 0], [0, 0], [0, 0]],
                [[0, 1], [0, 2], [-1, -1]],
                [[0, 0], [0, 0], [-1, -1]],
                # FIXME this depends on "mixed ploidy" interpretation.
                [[0, -2], [0, 1], [0, 2]],
            ],
            dtype="i1",
        )
        nt.assert_array_equal(ds["call_genotype"], call_genotype)
        nt.assert_array_equal(ds["call_genotype_mask"], call_genotype < 0)

    def test_call_genotype_phased(self, ds):
        call_genotype_phased = np.array(
            [
                [True, True, False],
                [True, True, False],
                [True, True, False],
                [True, True, False],
                [True, True, False],
                [True, True, False],
                [False, False, False],
                [False, True, False],
                [True, False, True],
            ],
            dtype=bool,
        )
        nt.assert_array_equal(ds["call_genotype_phased"], call_genotype_phased)

    def test_call_DP(self, ds):
        call_DP = [
            [-1, -1, -1],
            [-1, -1, -1],
            [1, 8, 5],
            [3, 5, 3],
            [6, 0, 4],
            [-1, 4, 2],
            [4, 2, 3],
            [-1, -1, -1],
            [-1, -1, -1],
        ]
        nt.assert_array_equal(ds["call_DP"], call_DP)

    def test_call_HQ(self, ds):
        call_HQ = [
            [[10, 15], [10, 10], [3, 3]],
            [[10, 10], [10, 10], [3, 3]],
            [[51, 51], [51, 51], [-1, -1]],
            [[58, 50], [65, 3], [-1, -1]],
            [[23, 27], [18, 2], [-1, -1]],
            [[56, 60], [51, 51], [-1, -1]],
            [[-1, -1], [-1, -1], [-1, -1]],
            [[-1, -1], [-1, -1], [-1, -1]],
            [[-1, -1], [-1, -1], [-1, -1]],
        ]
        nt.assert_array_equal(ds["call_HQ"], call_HQ)

    def test_no_genotypes(self, ds, tmp_path):
        path = "tests/data/vcf/sample_no_genotypes.vcf.gz"
        out = tmp_path / "example.vcf.zarr"
        vcf.convert_vcf([path], out)
        ds2 = sg.load_dataset(out)
        assert len(ds2["sample_id"]) == 0
        for col in ds:
            if col != "sample_id" and not col.startswith("call_"):
                xt.assert_equal(ds[col], ds2[col])

    @pytest.mark.parametrize(
        ["chunk_length", "chunk_width", "y_chunks", "x_chunks"],
        [
            (1, 1, (1, 1, 1, 1, 1, 1, 1, 1, 1), (1, 1, 1)),
            (2, 2, (2, 2, 2, 2, 1), (2, 1)),
            (3, 3, (3, 3, 3), (3,)),
            (4, 3, (4, 4, 1), (3,)),
        ],
    )
    def test_chunk_size(
        self, ds, tmp_path, chunk_length, chunk_width, y_chunks, x_chunks
    ):
        out = tmp_path / "example.vcf.zarr"
        vcf.convert_vcf(
            [self.data_path], out, chunk_length=chunk_length, chunk_width=chunk_width
        )
        ds2 = sg.load_dataset(out)
        # print(ds2.call_genotype.values)
        # print(ds.call_genotype.values)
        xt.assert_equal(ds, ds2)
        assert ds2.call_DP.chunks == (y_chunks, x_chunks)
        assert ds2.call_GQ.chunks == (y_chunks, x_chunks)
        assert ds2.call_HQ.chunks == (y_chunks, x_chunks, (2,))
        assert ds2.call_genotype.chunks == (y_chunks, x_chunks, (2,))
        assert ds2.call_genotype_mask.chunks == (y_chunks, x_chunks, (2,))
        assert ds2.call_genotype_phased.chunks == (y_chunks, x_chunks)
        assert ds2.variant_AA.chunks == (y_chunks,)
        assert ds2.variant_AC.chunks == (y_chunks, (2,))
        assert ds2.variant_AF.chunks == (y_chunks, (2,))
        assert ds2.variant_DB.chunks == (y_chunks,)
        assert ds2.variant_DP.chunks == (y_chunks,)
        assert ds2.variant_NS.chunks == (y_chunks,)
        assert ds2.variant_allele.chunks == (y_chunks, (4,))
        assert ds2.variant_contig.chunks == (y_chunks,)
        assert ds2.variant_filter.chunks == (y_chunks, (3,))
        assert ds2.variant_id.chunks == (y_chunks,)
        assert ds2.variant_id_mask.chunks == (y_chunks,)
        assert ds2.variant_position.chunks == (y_chunks,)
        assert ds2.variant_quality.chunks == (y_chunks,)
        assert ds2.contig_id.chunks == ((3,),)
        assert ds2.filter_id.chunks == ((3,),)
        assert ds2.sample_id.chunks == (x_chunks,)

    @pytest.mark.parametrize("worker_processes", [0, 1, 2])
    def test_worker_processes(self, ds, tmp_path, worker_processes):
        out = tmp_path / "example.vcf.zarr"
        vcf.convert_vcf(
            [self.data_path], out, chunk_length=3, worker_processes=worker_processes
        )
        ds2 = sg.load_dataset(out)
        xt.assert_equal(ds, ds2)

    @pytest.mark.parametrize("worker_processes", [0, 1, 2])
    def test_full_pipeline(self, ds, tmp_path, worker_processes):
        exploded = tmp_path / "example.exploded"
        vcf.explode(
            [self.data_path],
            exploded,
            worker_processes=worker_processes,
        )
        schema = tmp_path / "schema.json"
        with open(schema, "w") as f:
            vcf.generate_spec(exploded, f)
        out = tmp_path / "example.zarr"
        vcf.to_zarr(exploded, out, schema, worker_processes=worker_processes)
        ds2 = sg.load_dataset(out)
        xt.assert_equal(ds, ds2)


class Test1000G2020Example:
    data_path = "tests/data/vcf/1kg_2020_chrM.vcf.gz"

    @pytest.fixture(scope="class")
    def ds(self, tmp_path_factory):
        out = tmp_path_factory.mktemp("data") / "example.vcf.zarr"
        vcf.convert_vcf([self.data_path], out, worker_processes=0)
        return sg.load_dataset(out)

    def test_position(self, ds):
        # fmt: off
        pos = [
            26, 35, 40, 41, 42, 46, 47, 51, 52, 53, 54, 55, 56,
            57, 58, 59, 60, 61, 62, 63, 64, 65, 66,
        ]
        # fmt: on
        nt.assert_array_equal(ds.variant_position.values, pos)

    def test_alleles(self, ds):
        alleles = [
            ["C", "T", "", "", ""],
            ["G", "A", "", "", ""],
            ["T", "C", "", "", ""],
            ["C", "T", "CT", "", ""],
            ["T", "TC", "C", "TG", ""],
            ["T", "C", "", "", ""],
            ["G", "A", "", "", ""],
            ["T", "C", "", "", ""],
            ["T", "C", "", "", ""],
            ["G", "A", "", "", ""],
            ["G", "A", "", "", ""],
            ["TA", "TAA", "T", "CA", "AA"],
            ["ATT", "*", "ATTT", "ACTT", "A"],
            ["T", "C", "G", "*", "TC"],
            ["T", "A", "C", "*", ""],
            ["T", "A", "", "", ""],
            ["T", "A", "", "", ""],
            ["C", "A", "T", "", ""],
            ["G", "A", "", "", ""],
            ["T", "C", "A", "", ""],
            ["C", "T", "CT", "A", ""],
            ["TG", "T", "CG", "TGG", "TCGG"],
            ["G", "T", "*", "A", ""],
        ]
        nt.assert_array_equal(ds.variant_allele.values, alleles)

    def test_variant_MLEAC(self, ds):
        MLEAC = np.array(
            [
                [2, -2, -2, -2],
                [2, -2, -2, -2],
                [2, -2, -2, -2],
                [16, 2, -2, -2],
                [10, 4, 2, -2],
                [2, -2, -2, -2],
                [4, -2, -2, -2],
                [4, -2, -2, -2],
                [2, -2, -2, -2],
                [2, -2, -2, -2],
                [2, -2, -2, -2],
                [2, 26, 12, 4],
                [26, 2, 8, 4],
                [11, 6, 4, 2],
                [26, 1, 4, -2],
                [2, -2, -2, -2],
                [2, -2, -2, -2],
                [2, 12, -2, -2],
                [14, -2, -2, -2],
                [4, 2, -2, -2],
                [320, 20, 2, -2],
                [12, 2, 6, 4],
                [18, 12, 4, -2],
            ],
            dtype=np.int16,
        )
        nt.assert_array_equal(ds.variant_MLEAC.values, MLEAC)

    def test_call_AD(self, ds):
        call_AD = [
            [[446, 0, -2, -2, -2], [393, 0, -2, -2, -2], [486, 0, -2, -2, -2]],
            [[446, 0, -2, -2, -2], [393, 0, -2, -2, -2], [486, 0, -2, -2, -2]],
            [[446, 0, -2, -2, -2], [393, 0, -2, -2, -2], [486, 0, -2, -2, -2]],
            [[446, 0, 0, -2, -2], [393, 0, 0, -2, -2], [486, 0, 0, -2, -2]],
            [[446, 0, 0, 0, -2], [393, 0, 0, 0, -2], [486, 0, 0, 0, -2]],
            [[446, 0, -2, -2, -2], [393, 0, -2, -2, -2], [486, 0, -2, -2, -2]],
            [[446, 0, -2, -2, -2], [393, 0, -2, -2, -2], [486, 0, -2, -2, -2]],
            [[446, 0, -2, -2, -2], [393, 0, -2, -2, -2], [486, 0, -2, -2, -2]],
            [[446, 0, -2, -2, -2], [393, 0, -2, -2, -2], [486, 0, -2, -2, -2]],
            [[446, 0, -2, -2, -2], [393, 0, -2, -2, -2], [486, 0, -2, -2, -2]],
            [[446, 0, -2, -2, -2], [393, 0, -2, -2, -2], [486, 0, -2, -2, -2]],
            [[446, 0, 0, 0, 0], [393, 0, 0, 0, 0], [486, 0, 0, 0, 0]],
            [[446, 0, 0, 0, 0], [393, 0, 0, 0, 0], [486, 0, 0, 0, 0]],
            [[446, 0, 0, 0, 0], [393, 0, 0, 0, 0], [486, 0, 0, 0, 0]],
            [[446, 0, 0, 0, -2], [393, 0, 0, 0, -2], [486, 0, 0, 0, -2]],
            [[446, 0, -2, -2, -2], [393, 0, -2, -2, -2], [486, 0, -2, -2, -2]],
            [[446, 0, -2, -2, -2], [393, 0, -2, -2, -2], [486, 0, -2, -2, -2]],
            [[446, 0, 0, -2, -2], [393, 0, 0, -2, -2], [486, 0, 0, -2, -2]],
            [[446, 0, -2, -2, -2], [393, 0, -2, -2, -2], [486, 0, -2, -2, -2]],
            [[446, 0, 0, -2, -2], [393, 0, 0, -2, -2], [486, 0, 0, -2, -2]],
            [[446, 0, 0, 0, -2], [393, 0, 0, 0, -2], [486, 0, 0, 0, -2]],
            [[446, 0, 0, 0, 0], [393, 0, 0, 0, 0], [486, 0, 0, 0, 0]],
            [[446, 0, 0, 0, -2], [393, 0, 0, 0, -2], [486, 0, 0, 0, -2]],
        ]
        nt.assert_array_equal(ds.call_AD.values, call_AD)

    def test_call_PID(self, ds):
        call_PGT = ds["call_PGT"].values
        assert np.all(call_PGT == ".")
        assert call_PGT.shape == (23, 3)


class Test1000G2020AnnotationsExample:
    data_path = "tests/data/vcf/1kg_2020_chr20_annotations.bcf"

    @pytest.fixture(scope="class")
    def ds(self, tmp_path_factory):
        out = tmp_path_factory.mktemp("data") / "example.zarr"
        # TODO capture warnings from htslib here
        vcf.convert_vcf([self.data_path], out, worker_processes=0)
        return sg.load_dataset(out)

    def test_position(self, ds):
        # fmt: off
        pos = [
            60070, 60083, 60114, 60116, 60137, 60138, 60149, 60181, 60183,
            60254, 60280, 60280, 60286, 60286, 60291, 60291, 60291, 60291,
            60291, 60329, 60331
        ]
        # fmt: on
        nt.assert_array_equal(ds.variant_position.values, pos)

    def test_alleles(self, ds):
        alleles = [
            ["G", "A"],
            ["T", "C"],
            ["T", "C"],
            ["A", "G"],
            ["T", "C"],
            ["T", "A"],
            ["C", "T"],
            ["A", "G"],
            ["A", "G"],
            ["C", "A"],
            ["TTTCCA", "T"],
            ["T", "TTTCCA"],
            ["T", "G"],
            ["TTCCAG", "T"],
            ["G", "T"],
            ["G", "GTCCAT"],
            ["GTCCATTCCAT", "G"],
            ["GTCCAT", "G"],
            ["G", "GTCCATTCCAT"],
            ["C", "G"],
            ["T", "C"],
        ]
        nt.assert_array_equal(ds.variant_allele.values, alleles)

    def test_info_fields(self, ds):
        info_vars = [
            "variant_1000Gp3_AA_GF",
            "variant_1000Gp3_AF",
            "variant_1000Gp3_HomC",
            "variant_1000Gp3_RA_GF",
            "variant_1000Gp3_RR_GF",
            "variant_AC",
            "variant_ACMG_GENE",
            "variant_ACMG_INHRT",
            "variant_ACMG_MIM_GENE",
            "variant_ACMG_PATH",
            "variant_AC_AFR",
            "variant_AC_AFR_unrel",
            "variant_AC_AMR",
            "variant_AC_AMR_unrel",
            "variant_AC_EAS",
            "variant_AC_EAS_unrel",
            "variant_AC_EUR",
            "variant_AC_EUR_unrel",
            "variant_AC_Het",
            "variant_AC_Het_AFR",
            "variant_AC_Het_AFR_unrel",
            "variant_AC_Het_AMR",
            "variant_AC_Het_AMR_unrel",
            "variant_AC_Het_EAS",
            "variant_AC_Het_EAS_unrel",
            "variant_AC_Het_EUR",
            "variant_AC_Het_EUR_unrel",
            "variant_AC_Het_SAS",
            "variant_AC_Het_SAS_unrel",
            "variant_AC_Hom",
            "variant_AC_Hom_AFR",
            "variant_AC_Hom_AFR_unrel",
            "variant_AC_Hom_AMR",
            "variant_AC_Hom_AMR_unrel",
            "variant_AC_Hom_EAS",
            "variant_AC_Hom_EAS_unrel",
            "variant_AC_Hom_EUR",
            "variant_AC_Hom_EUR_unrel",
            "variant_AC_Hom_SAS",
            "variant_AC_Hom_SAS_unrel",
            "variant_AC_SAS",
            "variant_AC_SAS_unrel",
            "variant_AF",
            "variant_AF_AFR",
            "variant_AF_AFR_unrel",
            "variant_AF_AMR",
            "variant_AF_AMR_unrel",
            "variant_AF_EAS",
            "variant_AF_EAS_unrel",
            "variant_AF_EUR",
            "variant_AF_EUR_unrel",
            "variant_AF_SAS",
            "variant_AF_SAS_unrel",
            "variant_AN",
            "variant_ANN",
            "variant_AN_AFR",
            "variant_AN_AFR_unrel",
            "variant_AN_AMR",
            "variant_AN_AMR_unrel",
            "variant_AN_EAS",
            "variant_AN_EAS_unrel",
            "variant_AN_EUR",
            "variant_AN_EUR_unrel",
            "variant_AN_SAS",
            "variant_AN_SAS_unrel",
            "variant_AR_GENE",
            "variant_BaseQRankSum",
            "variant_CADD_phred",
            "variant_CLNDBN",
            "variant_CLNDSDB",
            "variant_CLNDSDBID",
            "variant_CLNSIG",
            "variant_COSMIC_CNT",
            "variant_ClippingRankSum",
            "variant_DP",
            "variant_DS",
            "variant_END",
            "variant_Entrez_gene_id",
            "variant_Essential_gene",
            "variant_ExAC_AF",
            "variant_ExcHet",
            "variant_ExcHet_AFR",
            "variant_ExcHet_AMR",
            "variant_ExcHet_EAS",
            "variant_ExcHet_EUR",
            "variant_ExcHet_SAS",
            "variant_FS",
            "variant_GDI",
            "variant_GDI-Phred",
            "variant_GERP++_NR",
            "variant_GERP++_RS",
            "variant_HWE",
            "variant_HWE_AFR",
            "variant_HWE_AFR_unrel",
            "variant_HWE_AMR",
            "variant_HWE_AMR_unrel",
            "variant_HWE_EAS",
            "variant_HWE_EAS_unrel",
            "variant_HWE_EUR",
            "variant_HWE_EUR_unrel",
            "variant_HWE_SAS",
            "variant_HWE_SAS_unrel",
            "variant_HaplotypeScore",
            "variant_InbreedingCoeff",
            "variant_LOF",
            "variant_LoFtool_score",
            "variant_ME",
            "variant_MGI_mouse_gene",
            "variant_MLEAC",
            "variant_MLEAF",
            "variant_MQ",
            "variant_MQ0",
            "variant_MQRankSum",
            "variant_MutationAssessor_pred",
            "variant_MutationTaster_pred",
            "variant_NEGATIVE_TRAIN_SITE",
            "variant_NMD",
            "variant_POSITIVE_TRAIN_SITE",
            "variant_Pathway(BioCarta)_short",
            "variant_Polyphen2_HDIV_pred",
            "variant_Polyphen2_HVAR_pred",
            "variant_QD",
            "variant_RAW_MQ",
            "variant_RVIS",
            "variant_RVIS_percentile",
            "variant_ReadPosRankSum",
            "variant_Regulome_dbSNP141",
            "variant_SIFT_pred",
            "variant_SOR",
            "variant_Uniprot_aapos_Polyphen2",
            "variant_Uniprot_id_Polyphen2",
            "variant_VQSLOD",
            "variant_VariantType",
            "variant_ZFIN_zebrafish_gene",
            "variant_ZFIN_zebrafish_phenotype_tag",
            "variant_culprit",
            "variant_dbSNPBuildID",
            "variant_phastCons20way_mammalian",
            "variant_phyloP20way_mammalian",
            "variant_repeats",
        ]
        # Verified with bcftools view -H | grep INFO
        assert len(info_vars) == 140
        standard_vars = [
            "variant_filter",
            "variant_contig",
            "variant_position",
            "variant_allele",
            "variant_id",
            "variant_id_mask",
            "variant_quality",
            "contig_id",
            "contig_length",
            "filter_id",
            "sample_id",
        ]
        assert sorted(list(ds)) == sorted(info_vars + standard_vars)

    def test_variant_ANN(self, ds):
        variant_ANN = [
            "A|intergenic_region|MODIFIER|DEFB125|ENSG00000178591|intergenic_region|ENSG00000178591|||n.60070G>A||||||",
            "C|intergenic_region|MODIFIER|DEFB125|ENSG00000178591|intergenic_region|ENSG00000178591|||n.60083T>C||||||",
            "C|intergenic_region|MODIFIER|DEFB125|ENSG00000178591|intergenic_region|ENSG00000178591|||n.60114T>C||||||",
            "G|intergenic_region|MODIFIER|DEFB125|ENSG00000178591|intergenic_region|ENSG00000178591|||n.60116A>G||||||",
            "C|intergenic_region|MODIFIER|DEFB125|ENSG00000178591|intergenic_region|ENSG00000178591|||n.60137T>C||||||",
            "A|intergenic_region|MODIFIER|DEFB125|ENSG00000178591|intergenic_region|ENSG00000178591|||n.60138T>A||||||",
            "T|intergenic_region|MODIFIER|DEFB125|ENSG00000178591|intergenic_region|ENSG00000178591|||n.60149C>T||||||",
            "G|intergenic_region|MODIFIER|DEFB125|ENSG00000178591|intergenic_region|ENSG00000178591|||n.60181A>G||||||",
            "G|intergenic_region|MODIFIER|DEFB125|ENSG00000178591|intergenic_region|ENSG00000178591|||n.60183A>G||||||",
            "A|intergenic_region|MODIFIER|DEFB125|ENSG00000178591|intergenic_region|ENSG00000178591|||n.60254C>A||||||",
            "T|intergenic_region|MODIFIER|DEFB125|ENSG00000178591|intergenic_region|ENSG00000178591|||n.60281_60285delTTCCA||||||",
            "TTTCCA|intergenic_region|MODIFIER|DEFB125|ENSG00000178591|intergenic_region|ENSG00000178591|||n.60280_60281insTTCCA||||||",
            "G|intergenic_region|MODIFIER|DEFB125|ENSG00000178591|intergenic_region|ENSG00000178591|||n.60286T>G||||||",
            "T|intergenic_region|MODIFIER|DEFB125|ENSG00000178591|intergenic_region|ENSG00000178591|||n.60287_60291delTCCAG||||||",
            "T|intergenic_region|MODIFIER|DEFB125|ENSG00000178591|intergenic_region|ENSG00000178591|||n.60291G>T||||||",
            "GTCCAT|intergenic_region|MODIFIER|DEFB125|ENSG00000178591|intergenic_region|ENSG00000178591|||n.60291_60292insTCCAT||||||",
            "G|intergenic_region|MODIFIER|DEFB125|ENSG00000178591|intergenic_region|ENSG00000178591|||n.60292_60301delTCCATTCCAT||||||",
            "G|intergenic_region|MODIFIER|DEFB125|ENSG00000178591|intergenic_region|ENSG00000178591|||n.60292_60296delTCCAT||||||",
            "GTCCATTCCAT|intergenic_region|MODIFIER|DEFB125|ENSG00000178591|intergenic_region|ENSG00000178591|||n.60291_60292insTCCATTCCAT||||||",
            "G|intergenic_region|MODIFIER|DEFB125|ENSG00000178591|intergenic_region|ENSG00000178591|||n.60329C>G||||||",
            "C|intergenic_region|MODIFIER|DEFB125|ENSG00000178591|intergenic_region|ENSG00000178591|||n.60331T>C||||||",
        ]
        nt.assert_array_equal(ds.variant_ANN.values, variant_ANN)


class TestGeneratedFieldsExample:
    data_path = "tests/data/vcf/field_type_combos.vcf.gz"

    @pytest.fixture(scope="class")
    def ds(self, tmp_path_factory):
        out = tmp_path_factory.mktemp("data") / "vcf.zarr"
        vcf.convert_vcf([self.data_path], out)
        return sg.load_dataset(out)

    def test_info_string1(self, ds):
        values = ds["variant_IS1"].values
        non_missing = values[values != "."]
        nt.assert_array_equal(non_missing, ["bc"])

    def test_info_char1(self, ds):
        values = ds["variant_IC1"].values
        non_missing = values[values != "."]
        nt.assert_array_equal(non_missing, "f")

    def test_info_string2(self, ds):
        values = ds["variant_IS2"].values
        missing = np.all(values == ".", axis=1)
        non_missing_rows = values[~missing]
        nt.assert_array_equal(
            non_missing_rows, [["hij", "d"], [".", "d"], ["hij", "."]]
        )

    # FIXME can't figure out how to do the row masking properly here
    # def test_format_string1(self, ds):
    #     values = ds["call_FS1"].values
    #     missing = np.all(values == ".", axis=1)
    #     non_missing_rows = values[~missing]
    #     print(non_missing_rows)
    #     # nt.assert_array_equal(non_missing_rows, [["bc"], ["."]])

    # def test_format_string2(self, ds):
    #     values = ds["call_FS2"].values
    #     missing = np.all(values == ".", axis=1)
    #     non_missing_rows = values[~missing]
    #     non_missing = [v for v in pcvcf["FORMAT/FS2"].values if v is not None]
    #     nt.assert_array_equal(non_missing[0], [["bc", "op"], [".", "op"]])
    #     nt.assert_array_equal(non_missing[1], [["bc", "."], [".", "."]])


@pytest.mark.parametrize(
    "name",
    [
        "sample.vcf.gz",
        "sample_no_genotypes.vcf.gz",
        "1kg_2020_chrM.vcf.gz",
        "field_type_combos.vcf.gz",
    ],
)
def test_by_validating(name, tmp_path):
    path = f"tests/data/vcf/{name}"
    out = tmp_path / "test.zarr"
    vcf.convert_vcf([path], out, worker_processes=0)
    vcf.validate(path, out)