# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from ast import Str
from typing import Dict, List, Optional, Union, Tuple

import json 
import aiohttp

from omni.services.browser.asset import BaseAssetStore, AssetModel, SearchCriteria, ProviderModel
from .constants import SETTING_STORE_ENABLE
from pathlib import Path

CURRENT_PATH = Path(__file__).parent
DATA_PATH = CURRENT_PATH.parent.parent.parent.parent.joinpath("data")

# The name of your company
PROVIDER_ID = "EcoPlants"
# The URL location of your API
STORE_URL = "https://api.prod.pbrmax.cn/en-US/asset/list" 


class TemplateAssetProvider(BaseAssetStore):
    """ 
        Asset provider implementation.
    """

    def __init__(self, ov_app="Kit", ov_version="na") -> None:
        super().__init__(PROVIDER_ID)
        self._ov_app = ov_app
        self._ov_version = ov_version

    async def _search(self, search_criteria: SearchCriteria) -> Tuple[List[AssetModel], bool]:
        """ Searches the asset store.

            This function needs to be implemented as part of an implementation of the BaseAssetStore.
            This function is called by the public `search` function that will wrap this function in a timeout.
        """
        params = {}
        categories_t = {
            '':[-10000],
            'VEHICLES': [309,311,312], 
            'VEGETATION': [156,153,152,154,155,137,138,139], 
            'FURNITURE,SEAT': [196], 
            'ARCHIVE,RESIDENTIAL': [191,192,194,195,201,179], 
            'ARCHIVE,INDUSTRIAL': [315,317,320,284,285,286], 
            'ARCHIVE,COMMERCIAL': [202,218,219,173,168,170,181], 
            'ARCHITECTURE,ROAD': [308,310,249], 
            'ARCHITECTURE,HOUSE': [264,274,275], 
            'ARCHITECTURE,BUILDING': [261,263,267], 
            'ARCHITECTURE,ARCHAEOLOGY': [270,260,259], 
            } 
        category_t=''
        # Setting for filter search criteria
        if search_criteria.filter.categories:
            # No category search, also use keywords instead
            categories = search_criteria.filter.categories
            for category in categories:
                if category.startswith("/"):
                    category = category[1:]
                category_keywords = category.split("/")
                category_t=",".join(category_keywords).upper()
        if(len(categories_t[category_t])<1):
            return
        # Setting for keywords search criteria
        # if search_criteria.keywords:
        #     params["keywords"] = ",".join(search_criteria.keywords)
        assets: List[AssetModel] = []
        for cate in categories_t[category_t]:
            filterP={}
            filterP["type"]="3d assets"
            if cate!=-10000:
                filterP["category_id"]=cate
                # params["filter"]=json.dumps({"category_id":cate}) 
            params["filter"]=filterP
            # Setting for page number search criteria
            if search_criteria.page.number:
                params["page"] = search_criteria.page.number

            # Setting for max number of items per page 
            if search_criteria.page.size:
                params["limit"] = search_criteria.page.size/len(categories_t[category_t])

            items = []
            headers = {'app-version': '2.0.0'}
            data=[]
            # TODO: Uncomment once valid Store URL has been provided
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{STORE_URL}", json=params, headers=headers) as resp:
                    result = await resp.read()
                    result = await resp.json()
                    data= result["data"]
  
            items=data["items"]
            # Create AssetModel based off of JSON data
            for item in items:
                product_url_t='https://pbrmax.cn/?activeIndex=0&query={"pageNum":' + str(data["page"]) + ',"assetId":"'+item["asset_uid"]+'"}'
                if cate!=-10000:
                    product_url_t='https://pbrmax.cn/?activeIndex=0&query={"pageNum":' + str(data["page"]) + ',"assetId":"'+item["asset_uid"]+'","filter":{"category":'+ str(cate) +',"type":"3d assets"}'+'}'
                assets.append(
                    AssetModel(
                        identifier=item["asset_uid"],
                        name=item["name"],
                        published_at="",
                        categories=[],
                        tags=[],
                        vendor=PROVIDER_ID,
                        product_url=product_url_t,
                        download_url="",
                        price=0.0,
                        thumbnail=item["preview"],
                    )
                )

        # Are there more assets that we can load?
        more = True
        if search_criteria.page.size and len(assets) < search_criteria.page.size:
            more = False

        return (assets, more)

    def provider(self) -> ProviderModel:
        """Return provider info"""
        return ProviderModel(
            name=PROVIDER_ID, icon=f"{DATA_PATH}/logo_placeholder.png", enable_setting=SETTING_STORE_ENABLE
        )
